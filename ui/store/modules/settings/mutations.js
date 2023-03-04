import { ERRORS } from "./enums";

export default {
  setLogPath(state, newValue) {
    state.logPath = newValue;

    const username = newValue.includes("\\") ? newValue.split("\\")[2] : newValue.split("/")[2];
    state.rootDownloadsPath = `C:\\Users\\${username}\\Downloads`;
  },
  setShutdownErrorMessage(state, newValue) {
    state.shutdownErrorMessage = newValue;
  },
  setShutdownErrorStatus(state, { errorType, latestCompatibleSwVersion }) {
    let error = `${ERRORS[errorType]}.`;
    if (latestCompatibleSwVersion) {
      state.installerLink = `https://downloads.curibio.com/software/StringrayController-Setup-prod-${latestCompatibleSwVersion}.exe`;
      error += " Please download the installer for the correct version here:";
    } else {
      state.installerLink = null;
      error += " Mantarray Controller is about to shutdown.";
    }
    state.shutdownErrorStatus = error;
    state.shutdownErrorMessage = error;
  },
  setSoftwareUpdateAvailable(state, bool) {
    state.softwareUpdateAvailable = bool;
  },
  setFirmwareUpdateAvailable(state, updateInfo) {
    state.firmwareUpdateAvailable = updateInfo.firmwareUpdateAvailable;
    state.firmwareUpdateDurMins = updateInfo.channelFwUpdate ? 5 : 1;
  },
  setAllowSWUpdateInstall(state, bool) {
    state.allowSWUpdateInstall = bool;
  },
  setConfirmationRequest(state, bool) {
    state.confirmationRequest = bool;
  },
  setUserAccounts(state, newValue) {
    state.userAccounts = newValue;
  },
  setStoredAccounts(state, { customerId, usernames }) {
    state.storedCustomerId = customerId;
    state.storedUsernames = usernames;
  },
  setActiveUserIndex(state, newValue) {
    state.activeUserIndex = newValue;
  },
  resetToDefault(state) {
    state.activeUserIndex = null;
  },
  setUserCredInputNeeded(state, bool) {
    state.userCredInputNeeded = bool;
  },
};
