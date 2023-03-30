import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import { ERROR_CODES } from "@/store/modules/system/enums";

const W3CWebSocket = require("websocket").w3cwebsocket;
export const socket = new W3CWebSocket("ws://localhost:4567");
/**
 * Create a ws plugin for a Vuex store
 * @param {socket} socket the ws instance to connect to the Vuex store
 * @return {function} function the Vuex store will use to connect the plugin to itself
 */
export default function createWebSocketPlugin(socket) {
  return (store) => {
    socket.onerror = function () {
      console.log("Error connecting to controller");
    };

    socket.onopen = function () {
      console.log("Connected to controller");
      // TODO need to execute a system state transition when this value changes ?
      store.commit("system/setIsConnectedToController", true);
    };
    socket.onclose = function () {
      console.log("Disconnected from controller");
      store.commit("system/setIsConnectedToController", false);
      if (!store.state.system.shutdownStatus && !store.state.system.systemErrorCode) {
        store.commit("system/setSystemErrorCode", { error_code: ERROR_CODES.CONTROLLER_CONNECTION_LOST });
      }
    };

    socket.onmessage = function (e) {
      if (typeof e.data === "string") {
        console.log(`Comm from controller: ${e.data}`); // allow-log

        const wsMessage = JSON.parse(e.data);

        switch (wsMessage.communication_type) {
          case "status_update":
            if ("system_status" in wsMessage) store.commit("system/setStatusUuid", wsMessage.system_status);
            if ("is_stimulating" in wsMessage) {
              store.commit(
                "stimulation/setStimStatus",
                wsMessage.is_stimulating ? STIM_STATUS.STIM_ACTIVE : STIM_STATUS.READY
              );
              store.commit("stimulation/setStimPlayState", wsMessage.is_stimulating);
            }
            break;
          case "stimulator_circuit_statuses":
            store.dispatch(
              "stimulation/checkStimulatorCircuitStatuses",
              wsMessage.stimulator_circuit_statuses
            );
            break;
          case "barcode_update":
            // eslint complains without this if condition wrapper for some reason
            if (wsMessage) {
              const barcodeType = wsMessage.barcode_type.split("_")[0] + "Barcode";
              store.dispatch("system/validateBarcode", {
                type: barcodeType,
                newValue: wsMessage.new_barcode,
              });
            }
            break;
          case "sw_update":
            if (wsMessage.allow_software_update !== undefined) {
              store.commit("system/setAllowSwUpdateInstall", wsMessage.allow_software_update);
            }
            if (wsMessage.software_update_available !== undefined) {
              const status = wsMessage.software_update_available ? "found" : "not found";
              console.log("Software update " + status); // allow-log
              store.commit("system/setSoftwareUpdateAvailable", wsMessage.software_update_available);
            }
            break;
          case "user_input_needed":
            store.commit("settings/userInputNeeded", true);
            break;
          case "firmware_update_available":
            console.log("Firmware update found"); // allow-log
            store.commit("system/setFirmwareUpdateAvailable", wsMessage.channel_fw_update);
            break;
          case "error":
            store.commit("system/setSystemErrorCode", wsMessage);
            break;
          case "command_response":
            console.log("Response received."); // allow-log
            break;
          default:
            console.log("Message unrecognized. Skipping..."); // allow-log
            break;
        }
      }
    };
  };
}
