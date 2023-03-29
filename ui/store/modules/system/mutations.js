// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
import { STATUS, ERROR_MESSAGES } from "./enums";

export default {
  setStatusUuid(state, newId) {
    if (state.statusUuid !== STATUS.ERROR_STATE) {
      state.statusUuid = newId;
    }
  },
  setSimulationStatus(state, newId) {
    state.simulationMode = newId;
  },
  setIsConnectedToController(state, isConnected) {
    state.isConnectedToController = isConnected;
  },
  setBarcodeManualMode(state, newValue) {
    state.barcodeManualMode = newValue;
  },
  setBarcode(state, { type, newValue, isValid }) {
    state.barcodes[type].value = newValue;
    state.barcodes[type].valid = isValid;
  },
  setShutdownStatus(state, bool) {
    state.shutdownStatus = bool;
  },
  setBarcodeWarning(state, bool) {
    state.barcodeWarning = bool;
  },
  setSystemErrorCode(state, msg) {
    state.systemErrorCode = msg.error_code;

    if (msg.latest_compatible_sw_version) {
      state.systemErrorMessage = "Please download the installer for the correct version here:";
      state.installerLink = `https://downloads.curibio.com/software/StingrayController-Setup-prod-${msg.latest_compatible_sw_version}.exe`;
    } else if (state.statusUuid === STATUS.UPDATE_ERROR_STATE) {
      state.systemErrorMessage = "Error during firmware update.";
    } else {
      state.systemErrorMessage =
        ERROR_MESSAGES[msg.error_code] || "Stingray Controller is about to shutdown.";
    }
  },
  setSoftwareUpdateAvailable(state, bool) {
    state.softwareUpdateAvailable = bool;
  },
  setFirmwareUpdateAvailable(state, channelFwUpdate) {
    state.firmwareUpdateAvailable = true;
    state.firmwareUpdateDurMins = channelFwUpdate ? 5 : 1;
  },
  setAllowSWUpdateInstall(state, bool) {
    state.allowSWUpdateInstall = bool;
  },
  setConfirmationRequest(state, bool) {
    state.confirmationRequest = bool;
  },
};
