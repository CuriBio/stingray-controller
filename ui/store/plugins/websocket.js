// import { ENUMS } from "../modules/playback/enums";

// const io = require("socket.io-client");

// export const socket = io("ws://localhost:4567"); // TODO use constant here

/**
 * Create a socket.io plugin for a Vuex store
 * @param {Socket} socket the socket.io instance to connect to the Vuex store
 * @return {function} function the Vuex store will use to connect the plugin to itself
 */
export default function createWebSocketPlugin(socket) {
  return (store) => {
    socket.on("stimulation_data", (stimJson, cb) => {
      // Tanner (12/20/21): may want to put the same checks here as are in the waveformData handler once stim waveforms are sent instead of subprotocol indices
      store.dispatch("stimulation/appendStimWaveforms", JSON.parse(stimJson));
      /* istanbul ignore else */
      if (cb) cb("action done"); // this callback is only used for testing. The backend will not send a callback
    });

    socket.on("stimulatorCircuitStatuses", (messageJson, cb) => {
      store.dispatch("stimulation/checkStimulatorCircuitStatuses", JSON.parse(messageJson));

      /* istanbul ignore else */
      if (cb) cb("action done"); // this callback is only used for testing. The backend will not send a callback
    });
    socket.on("barcode", (messageJson, cb) => {
      if (!store.state.flask.barcodeManualMode) {
        const message = JSON.parse(messageJson);
        for (const barcodeType in store.state.playback.barcodes)
          if (message[barcodeType])
            store.dispatch("playback/validateBarcode", {
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
        store.commit("settings/setAllowSwUpdateInstall", message.allow_software_update);
      }
      if (message.softwareUpdateAvailable !== undefined) {
        const status = message.softwareUpdateAvailable ? "found" : "not found";
        console.log("Software update " + status); // allow-log
        store.commit("settings/setSoftwareUpdateAvailable", message.softwareUpdateAvailable);
      }

      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });
    socket.on("fw_update", (messageJson, cb) => {
      const message = JSON.parse(messageJson);
      if (message.firmwareUpdateAvailable === true) {
        console.log("Firmware update found"); // allow-log
        store.commit("settings/setFirmwareUpdateAvailable", message);
      }

      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });

    socket.on("error", async (messageJson, cb) => {
      const message = JSON.parse(messageJson);
      await store.commit("settings/setShutdownErrorStatus", message);
      /* istanbul ignore else */
      if (cb) cb("commit done"); // this callback is only used for testing. The backend will not send a callback
    });
  };
}
