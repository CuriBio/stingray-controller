// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
import { STATUS } from "./enums";
// import { ERRORS } from "./enums";

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
  setBarcodeWarning(state, bool) {
    state.barcodeWarning = bool;
  },
  setShutdownErrorMessage(state, newValue) {
    state.shutdownErrorMessage = newValue;
  },
  setShutdownErrorStatus(state, msg) {
    let error = `Error Code: ${msg.error_code}`; // `${ERRORS[errorType]}.`;
    if (msg.latest_compatible_sw_version) {
      state.installerLink = `https://downloads.curibio.com/software/StingrayController-Setup-prod-${msg.latest_compatible_sw_version}.exe`;
      error += " Please download the installer for the correct version here:";
    } else {
      state.installerLink = null;
      error += " Stingray Controller is about to shutdown.";
    }
    state.shutdownErrorStatus = error;
    state.shutdownErrorMessage = error;
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
