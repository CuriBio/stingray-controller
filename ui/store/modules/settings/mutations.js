export default {
  setLogPath(state, newValue) {
    state.logPath = newValue;

    const username = newValue.includes("\\") ? newValue.split("\\")[2] : newValue.split("/")[2];
    state.rootDownloadsPath = `C:\\Users\\${username}\\Downloads`;
  },
  setUserAccount(state, newValue) {
    state.userAccount = { ...newValue };
  },
  setStoredAccounts(state, { customerId, usernames }) {
    state.storedCustomerId = customerId;
    state.storedUsernames = usernames;
  },
  setUserCredInputNeeded(state, bool) {
    state.userCredInputNeeded = bool;
  },
};
