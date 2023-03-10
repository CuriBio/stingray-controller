const io = require("socket.io-client");

export const socket = io("ws://localhost:4567"); // TODO use constant here

/**
 * Create a socket.io plugin for a Vuex store
 * @param {Socket} socket the socket.io instance to connect to the Vuex store
 * @return {function} function the Vuex store will use to connect the plugin to itself
 */
export default function createWebSocketPlugin(socket) {
  return (store) => {
    socket.on("stimulatorCircuitStatuses", (messageJson, cb) => {
      store.dispatch("stimulation/checkStimulatorCircuitStatuses", JSON.parse(messageJson));

      /* istanbul ignore else */
      if (cb) cb("action done"); // this callback is only used for testing. The backend will not send a callback
    });

    socket.on("barcode", (messageJson, cb) => {
      if (!store.state.system.barcodeManualMode) {
        const message = JSON.parse(messageJson);
        for (const barcodeType in store.state.system.barcodes)
          if (message[barcodeType])
            store.dispatch("system/validateBarcode", {
              type: barcodeType,
              newValue: message[barcodeType],
            });
      }

      /* istanbul ignore else */
      if (cb) cb("action done"); // this callback is only used for testing. The backend will not send a callback
    });

    socket.on("sw_update", (messageJson, cb) => {
      const message = JSON.parse(messageJson);
      if (message.allow_software_update !== undefined) {
        store.commit("system/setAllowSwUpdateInstall", message.allow_software_update);
      }
      if (message.softwareUpdateAvailable !== undefined) {
        const status = message.softwareUpdateAvailable ? "found" : "not found";
        console.log("Software update " + status); // allow-log
        store.commit("system/setSoftwareUpdateAvailable", message.softwareUpdateAvailable);
      }

      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });
    socket.on("fw_update", (messageJson, cb) => {
      const message = JSON.parse(messageJson);
      if (message.firmwareUpdateAvailable === true) {
        console.log("Firmware update found"); // allow-log
        store.commit("system/setFirmwareUpdateAvailable", message);
      }

      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });
    socket.on("system_status", async (messageJson, cb) => {
      const statusUuid = JSON.parse(messageJson);
      await store.commit("system/setStatusUuid", statusUuid);
      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });
    socket.on("error", async (messageJson, cb) => {
      const message = JSON.parse(messageJson);
      await store.commit("system/setShutdownErrorStatus", message);
      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });
  };
}
