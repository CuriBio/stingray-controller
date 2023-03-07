import actions from "./actions";
import getters from "./getters";
import mutations from "./mutations";
import { ERRORS } from "./enums";

const defaultState = {
  logPath: "C:\\Users\\username\\AppData\\Roaming\\StingrayController\\logslask",
  rootDownloadsPath: "C:\\Users\\username\\Downloads",
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
