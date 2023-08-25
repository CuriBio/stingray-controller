import { ERROR_CODES, SYSTEM_STATUS } from "@/store/modules/system/enums";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import { TextValidation } from "@/js-utils/TextValidation.js";

const TextValidationPlateBarcode = new TextValidation("plateBarcode");

const W3CWebSocket = require("websocket").w3cwebsocket;

export default {
  async connectToController({ state }, numRetriesLeft) {
    // Tanner (4/6/23): need to grab these values this way, destructuring from the value passed into this function does not seem to work
    const { commit, dispatch } = this;

    // guarding to be extra safe
    if (state.socket !== null) return;

    const socket = new W3CWebSocket("ws://localhost:4565");

    socket.onerror = function() {
      const baseLogMsg = "Error connecting to controller. ";

      if (numRetriesLeft) {
        console.log(baseLogMsg + "Retrying...");

        const retryConnection = () => {
          dispatch("system/connectToController", numRetriesLeft - 1);
        };
        setTimeout(retryConnection, 1000);
      } else {
        console.error(baseLogMsg + "Max num retries hit");
        commit("system/setSystemErrorCode", { error_code: ERROR_CODES.CONTROLLER_CONNECTION_CREATION });
      }
    };

    socket.onopen = function() {
      console.log("Connected to controller");
      // Tanner (3/30/23): make sure to set the socket before updating isConnectedToController
      commit("system/setSocket", socket);
      commit("system/setIsConnectedToController", true);
    };

    socket.onclose = function() {
      if (!state.isConnectedToController) return;

      console.log("Disconnected from controller");
      commit("system/setIsConnectedToController", false);
      // Tanner (3/30/23): if shutdownStatus is not set (meaning the user didn't close out on their own), and no error code is set
      // (meaning that the controller didn't report an error before it shut down), then the controller disconnected
      // unexpectedly and the corresponding error should be set
      if (!state.shutdownStatus && !state.systemErrorCode) {
        commit("system/setSystemErrorCode", { error_code: ERROR_CODES.CONTROLLER_CONNECTION_LOST });
      }
    };

    socket.onmessage = function(e) {
      if (typeof e.data === "string") {
        console.log(`Comm from controller: ${e.data}`); // allow-log

        const wsMessage = JSON.parse(e.data);

        // TODO catch all errors here and report correct error code
        switch (wsMessage.communication_type) {
          case "status_update":
            if ("system_status" in wsMessage) commit("system/setStatusUuid", wsMessage.system_status);
            // want to start stim if not already started if offline mode status is sent
            // stim will initially be inactive if booting up SW in offline mode
            if (
              "stimulation_protocols_running" in wsMessage ||
              wsMessage.system_status === SYSTEM_STATUS.OFFLINE_STATE
            ) {
              const stimPlayState =
                ("stimulation_protocols_running" in wsMessage &&
                  wsMessage.stimulation_protocols_running.includes(true)) ||
                wsMessage.system_status === SYSTEM_STATUS.OFFLINE_STATE;

              commit(
                "stimulation/setStimStatus",
                stimPlayState ? STIM_STATUS.STIM_ACTIVE : STIM_STATUS.READY
              );
              commit("stimulation/setStimPlayState", stimPlayState);
            }
            break;
          case "stimulator_circuit_statuses":
            dispatch("stimulation/checkStimulatorCircuitStatuses", wsMessage.stimulator_circuit_statuses);
            break;
          case "barcode_update":
            // eslint complains without this if condition wrapper for some reason
            if (wsMessage) {
              const barcodeType = wsMessage.barcode_type.split("_")[0] + "Barcode";
              dispatch("system/validateBarcode", {
                type: barcodeType,
                newValue: wsMessage.new_barcode
              });
            }
            break;
          case "end_offline_mode":
            dispatch("stimulation/populateStimAfterOffline", wsMessage);
            break;
          case "sw_update":
            if (wsMessage.allow_software_update !== undefined) {
              commit("system/setallowSwUpdateInstall", wsMessage.allow_software_update);
            }
            if (wsMessage.software_update_available !== undefined) {
              const status = wsMessage.software_update_available ? "found" : "not found";
              console.log("Software update " + status); // allow-log
              commit("system/setSoftwareUpdateAvailable", wsMessage.software_update_available);
            }
            break;
          case "user_input_needed":
            // user creds are the only user input that will ever be required at the moment
            commit("settings/setUserCredInputNeeded", true);
            break;
          case "login_result":
            commit("system/setLoginAttemptStatus", wsMessage.success);
            break;
          case "firmware_update_available":
            console.log("Firmware update found"); // allow-log
            commit("system/setFirmwareUpdateAvailable", wsMessage.channel_fw_update);
            break;
          case "error":
            commit("system/setSystemErrorCode", wsMessage);
            break;
          case "command_response":
            // TODO is this necessary?
            console.log("Response received."); // allow-log
            break;
          default:
            console.error(`Unrecognized comm type: ${wsMessage.communication_type}`); // allow-log
            break;
        }
      }
    };
  },

  async validateBarcode({ commit, state }, { type, newValue }) {
    const result = TextValidationPlateBarcode.validate(newValue, type);
    const isValid = result == "";

    // stop all running processes if either barcode changes regardless of validity
    if (this.state.stimulation.stimPlayState) {
      await this.dispatch("stimulation/stopStimulation");
      commit("setBarcodeWarning", true);
    }
    // require new stim configuration check if either new barcode changes
    if (isValid && state.barcodes[type].value !== newValue) {
      this.commit("stimulation/setStimStatus", STIM_STATUS.CONFIG_CHECK_NEEDED);
    }

    commit("setBarcode", { type, newValue, isValid });
  },
  async sendFirmwareUpdateConfirmation({ state }, updateAccepted) {
    const status = updateAccepted ? "accepted" : "declined";
    console.log(`User ${status} firmware update`); // allow-log

    const wsMessage = JSON.stringify({
      command: "set_firmware_update_confirmation",
      update_accepted: updateAccepted
    });

    state.socket.send(wsMessage);
  },
  async sendSetLatestSwVersion({ state }, latestSwVersionAvailable) {
    const wsMessage = JSON.stringify({
      command: "set_latest_software_version",
      version: latestSwVersionAvailable
    });

    state.socket.send(wsMessage);
  },
  async sendShutdown({ commit, state }) {
    console.log("User initiated shutdown"); // allow-log

    commit("setShutdownStatus", true);

    const wsMessage = JSON.stringify({
      command: "shutdown"
    });

    state.socket.send(wsMessage);
  },
  async sendOfflineState({ state }) {
    const offlineState = state.statusUuid !== SYSTEM_STATUS.OFFLINE_STATE;
    // this can only be called if stimulation is already active
    const wsMessage = JSON.stringify({
      command: "set_offline_state",
      offline_state: offlineState
    });

    if (offlineState) {
      this.commit("stimulation/resetState");
      this.commit("stimulation/setProtocolList", [{ letter: "", color: "", label: "Create New" }]);
    }

    state.socket.send(wsMessage);
  }
};
