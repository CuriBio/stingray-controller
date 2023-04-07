import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import { settingsStoreModule } from "@/dist/stingray.common";

describe("store/settings", () => {
  const localVue = createLocalVue();
  localVue.use(Vuex);
  let NuxtStore;
  let store;

  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });
  afterEach(async () => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  test("When initialized, Then the userAccounts is an empty with no value assigned", () => {
    const arrayOfUserAccounts = store.state.settings.userAccounts;
    expect(arrayOfUserAccounts).toHaveLength(0);
  });
  test("When initialized, Then the userAccounts when accessed via settingsStoreModule is an empty with no value assigned", () => {
    const arrayOfUserAccounts = store.state.settings.userAccounts;
    expect(arrayOfUserAccounts).toHaveLength(0);
  });

  test("When initialized the array of userAccounts is empty and size 0, Then commit a single valid userAccount as the first record in userAccounts, activeUserIndex/activeUserIndex and assert the same", () => {
    const arrayOfUserAccounts = [
      {
        customerId: "4vqyd62oARXqj9nRUNhtLQ",
        userPassword: "941532a0-6be1-443a-a9d5-d57bdf180a52",
        username: "User account -1",
      },
    ];
    expect(store.state.settings.userAccounts).toHaveLength(0);
    store.commit("settings/setUserAccounts", arrayOfUserAccounts);
    store.commit("settings/setActiveUserIndex", 0);
    expect(store.state.settings.userAccounts[store.state.settings.activeUserIndex].customerId).toStrictEqual(
      "4vqyd62oARXqj9nRUNhtLQ"
    );
    expect(
      store.state.settings.userAccounts[store.state.settings.activeUserIndex].userPassword
    ).toStrictEqual("941532a0-6be1-443a-a9d5-d57bdf180a52");
    expect(store.state.settings.userAccounts[store.state.settings.activeUserIndex].username).toStrictEqual(
      "User account -1"
    );
  });
  test("When initialized the array of userAccounts is empty and size 0, Then commit an array of customer details in userAccounts and assert the number of customer records", () => {
    const arrayOfUserAccounts = [
      {
        customerId: "4vqyd62oARXqj9nRUNhtLQ",
        userPassword: "941532a0-6be1-443a-a9d5-d57bdf180a52",
        username: "User account -1",
      },
      {
        customerId: "6cBaidlJ84Ggc5JA7IYCgv",
        userPassword: "941532a0-6be1-443a-cdee-d57bdf180a52",
        username: "User account -1",
      },
    ];
    expect(store.state.settings.userAccounts).toHaveLength(0);
    store.commit("settings/setUserAccounts", arrayOfUserAccounts);
    expect(store.state.settings.userAccounts).toHaveLength(2);
  });
  test("Given the store has multiple customer details, When the mutation deletes one Customer details, Then validate the number of the customer decrements by one", () => {
    /* ========================== */
    /* |  Settings.vue          | */
    /* |  (Edit Customer)       |    -------- >  ======================== */
    /* |                        |                | EditUser.vue      | */
    /* |                        |    < --------  |  (Delete ID)         | */
    /* |  (SaveChanges)         |                ======================== */
    /* ========================== */

    const arrayOfUserAccounts = [
      {
        customerId: "4vqyd62oARXqj9nRUNhtLQ",
        userPassword: "941532a0-6be1-443a-a9d5-d57bdf180a52",
        username: "User account -1",
      },
      {
        customerId: "6cBaidlJ84Ggc5JA7IYCgv",
        userPassword: "941532a0-6be1-443a-cdee-d57bdf180a52",
        username: "User account -2",
      },
    ];
    expect(store.state.settings.userAccounts).toHaveLength(0);
    store.commit("settings/setUserAccounts", arrayOfUserAccounts);

    /* User now does Edit Customer Click on the "User account - 1*/
    store.commit("settings/setActiveUserIndex", 0);
    const currentFocusCustomerid = store.state.settings.userAccounts[0];
    expect(currentFocusCustomerid.username).toStrictEqual("User account -1");
    expect(currentFocusCustomerid.customerId).toStrictEqual("4vqyd62oARXqj9nRUNhtLQ");
    expect(currentFocusCustomerid.userPassword).toStrictEqual("941532a0-6be1-443a-a9d5-d57bdf180a52");
    /*  (Delete ID) selected */
    const currentCustomerids = store.state.settings.userAccounts;
    const focusActiveUserIndex = store.state.settings.activeUserIndex;
    /* Javascript array provides an internal api array.splice(idx,1)  so we delete object in array and store in Vuex*/
    currentCustomerids.splice(focusActiveUserIndex, 1);
    /*  (SaveChanges) selected */
    store.commit("settings/setUserAccounts", currentCustomerids);
    const updatedFocusCustomerid = store.state.settings.userAccounts[0];
    expect(updatedFocusCustomerid.customerId).toStrictEqual("6cBaidlJ84Ggc5JA7IYCgv");
    expect(updatedFocusCustomerid.userPassword).toStrictEqual("941532a0-6be1-443a-cdee-d57bdf180a52");
    expect(updatedFocusCustomerid.username).toStrictEqual("User account -2");
    expect(store.state.settings.userAccounts).toHaveLength(1);
  });
  test("When a user resets the settings form, Then the mutation will only reset current selection and toggle switches and will not reset existing IDs", async () => {
    const arrayOfUserAccounts = [
      {
        customerId: "4vqyd62oARXqj9nRUNhtLQ",
        userPassword: "941532a0-6be1-443a-a9d5-d57bdf180a52",
        username: "User account -1",
      },
    ];

    store.commit("settings/setUserAccounts", arrayOfUserAccounts);
    expect(store.state.settings.userAccounts).toHaveLength(1);
    store.commit("settings/setActiveUserIndex", 0);
    await store.commit("settings/resetToDefault");

    expect(store.state.settings.userAccounts).toHaveLength(1);
    expect(store.state.settings.activeUserIndex).toBeNull();
  });

  test("When the app is created and the user's log path is committed, Then the base downloads path also gets updated with username", async () => {
    const testWinPath = "C:\\Users\\CuriBio\\TestPath";
    const expectedWinBasePath = "C:\\Users\\CuriBio\\Downloads";

    store.commit("settings/setLogPath", testWinPath);

    const { logPath, rootDownloadsPath } = store.state.settings;
    expect(logPath).toBe(testWinPath);
    expect(rootDownloadsPath).toBe(expectedWinBasePath);

    const testPath = "/Users/CuriBio/TestPath";
    const expectedDownloadsBasePath = "C:\\Users\\CuriBio\\Downloads";

    store.commit("settings/setLogPath", testPath);

    expect(store.state.settings.logPath).toBe(testPath);
    expect(store.state.settings.rootDownloadsPath).toBe(expectedDownloadsBasePath);
  });
});
