import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
const testUserAccount = {
  customerId: "4vqyd62oARXqj9nRUNhtLQ",
  password: "941532a0-6be1-443a-a9d5-d57bdf180a52",
  username: "User account -1",
};
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

  test("When initialized, Then the userAccount is an empty with no value assigned", () => {
    expect(store.state.settings.userAccount).toStrictEqual({ customerId: "", username: "", password: "" });
  });

  test("Given the store has multiple customer details, When the mutation deletes one Customer details, Then validate the number of the customer decrements by one", () => {
    /* ========================== */
    /* |  Settings.vue          | */
    /* |  (Edit Customer)       |    -------- >  ======================== */
    /* |                        |                | EditUser.vue      | */
    /* |                        |    < --------  |  (Delete ID)         | */
    /* |  (SaveChanges)         |                ======================== */
    /* ========================== */

    store.commit("settings/setUserAccount", testUserAccount);

    /* User now does Edit Customer Click on the "User account - 1*/
    const currentFocusAccount = store.state.settings.userAccount;
    expect(currentFocusAccount.username).toStrictEqual("User account -1");
    expect(currentFocusAccount.customerId).toStrictEqual("4vqyd62oARXqj9nRUNhtLQ");
    expect(currentFocusAccount.password).toStrictEqual("941532a0-6be1-443a-a9d5-d57bdf180a52");
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
