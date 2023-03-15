export default {
  setLogPath(state, newValue) {
    state.logPath = newValue;

    const username = newValue.includes("\\") ? newValue.split("\\")[2] : newValue.split("/")[2];
    state.rootDownloadsPath = `C:\\Users\\${username}\\Downloads`;
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
