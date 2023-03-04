import actions from "./actions";
import getters from "./getters";
import mutations from "./mutations";
import { ERRORS } from "./enums";

const defaultState = {
  logPath: "C:\\Users\\username\\AppData\\Roaming\\StringrayController\\logsFlask",
  rootDownloadsPath: "C:\\Users\\username\\Downloads",
  shutdownErrorMessage: "Stringray software is about to shut down.",
  shutdownErrorStatus: "",
  installerLink: null,
  softwareUpdateAvailable: false,
  firmwareUpdateAvailable: false,
  firmwareUpdateDurMins: null,
  allowSWUpdateInstall: false,
  confirmationRequest: false,
  userCredInputNeeded: false,
  userAccounts: [],
  storedCustomerId: null,
  storedUsernames: [],
  activeUserIndex: null,
};

const state = () => JSON.parse(JSON.stringify(defaultState));

export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters,
  ERRORS,
};
