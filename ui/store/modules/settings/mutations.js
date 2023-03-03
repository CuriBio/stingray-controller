import { ERRORS } from "./enums";

export default {
  setLogPath(state, new_value) {
    state.logPath = new_value;

    const username = new_value.includes("\\") ? new_value.split("\\")[2] : new_value.split("/")[2];
    state.rootDownloadsPath = `C:\\Users\\${username}\\Downloads`;
  },
  setShutdownErrorMessage(state, new_value) {
    state.shutdownErrorMessage = new_value;
  },
  setShutdownErrorStatus(state, { error_type, latest_compatible_sw_version }) {
    let error = `${ERRORS[error_type]}.`;
    if (latest_compatible_sw_version) {
      state.installerLink = `https://downloads.curibio.com/software/StringrayController-Setup-prod-${latest_compatible_sw_version}.exe`;
      error += " Please download the installer for the correct version here:";
    } else {
      state.installerLink = null;
      error += " Mantarray Controller is about to shutdown.";
    }
    state.shutdownErrorStatus = error;
    state.shutdownErrorMessage = error;
  },
  setBeta2Mode(state, bool) {
    state.beta2Mode = bool;
  },
  setSoftwareUpdateAvailable(state, bool) {
    state.softwareUpdateAvailable = bool;
  },
  setFirmwareUpdateAvailable(state, update_info) {
    state.firmwareUpdateAvailable = update_info.firmwareUpdateAvailable;
    state.firmwareUpdateDurMins = update_info.channel_fw_update ? 5 : 1;
  },
  setAllowSWUpdateInstall(state, bool) {
    state.allowSWUpdateInstall = bool;
  },
  setConfirmationRequest(state, bool) {
    state.confirmationRequest = bool;
  },
};
