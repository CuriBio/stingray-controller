import { STIM_STATUS } from "@/store/modules/stimulation/enums";

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
      console.log("Connection Error");
    };

    socket.onopen = function () {
      console.log("WS Client Connected");
    };

    socket.onclose = function () {
      console.log("WS Client Closed");
    };

    socket.onmessage = function (e) {
      if (typeof e.data === "string") {
        const wsMessage = JSON.parse(e.data);
        const { content } = wsMessage;
        console.log("WS Received: '" + e.data + "'"); // allow-log

        switch (wsMessage.communication_type) {
          case "status_update":
            if ("system_status" in wsMessage) store.commit("system/setStatusUuid", wsMessage.system_status);
            if ("is_stimulating" in wsMessage) {
              store.commit("stimulation/setStimStatus");
              store.commit(
                "stimulation/setStimPlayState",
                wsMessage.is_stimulating ? STIM_STATUS.STIM_ACTIVE : STIM_STATUS.READY
              );
            }
            break;
          case "stimulator_circuit_statuses":
            store.dispatch("stimulation/checkStimulatorCircuitStatuses", content);
            break;
          case "barcodes":
            for (const barcodeType in store.state.system.barcodes) {
              if (content[barcodeType])
                store.dispatch("system/validateBarcode", {
                  type: barcodeType,
                  newValue: content[barcodeType],
                });
            }
            break;
          case "sw_update":
            if (content.allow_software_update !== undefined) {
              store.commit("system/setAllowSwUpdateInstall", content.allow_software_update);
            }
            if (content.softwareUpdateAvailable !== undefined) {
              const status = content.softwareUpdateAvailable ? "found" : "not found";
              console.log("Software update " + status); // allow-log
              store.commit("system/setSoftwareUpdateAvailable", content.softwareUpdateAvailable);
            }
            break;
          case "fw_update":
            if (content.firmwareUpdateAvailable) {
              console.log("Firmware update found"); // allow-log
              store.commit("system/setFirmwareUpdateAvailable", content);
            }
            break;
          case "error":
            // TODO might be different or need to change
            store.commit("system/setShutdownErrorStatus", content);
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
