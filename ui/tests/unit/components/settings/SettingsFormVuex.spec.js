import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/settings/SettingsForm.vue";
import { SettingsForm as DistComponentToTest } from "@/dist/stingray.common";
import { socket } from "@/store/plugins/websocket"; // TODO need to grab this value from the store now
import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import BootstrapVue from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.min.css";
import { arrayOfUserAccounts } from "./SettingsFormUserData.js";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(BootstrapVue);

let NuxtStore;
let store;

describe("SettingsForm.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => wrapper.destroy());

  // TODO figure out what these are actually trying to test
  const arrayOfUserAccountsMissingUserIds = [
    {
      customerId: "4vqyd62oARXqj9nRUNhtLQ",
      userPassword: "941532a0-6be1-443a-a9d5-d57bdf180a52",
      userName: "User account -1",
    },
  ];
  const arrayOfCustomeridNullMissingUserIds = [
    {
      customerId: "4vqyd62oARXqj9nRUNhtLQ",
      userPassword: "941532a0-6be1-443a-a9d5-d57bdf180a52",
      userName: "",
    },
  ];

  test("When mounting SettingsForm from the build dist file, Then verify that it loads successfully", () => {
    const propsData = null;
    wrapper = mount(DistComponentToTest, {
      propsData,
      store,
      localVue,
    });

    const targetSpan = wrapper.find(".span__settingsform-title");

    expect(targetSpan.text()).toStrictEqual("Settings");
  });

  describe("Given Vuex has valid customer and user accounts but no customer index or user index selected", () => {
    beforeEach(() => {
      // commit a deep copy of the template object to the Vuex store using JSON stringify/parse, as it may be modified during tests. https://www.javascripttutorial.net/object/3-ways-to-copy-objects-in-javascript/
      store.commit("settings/setUserAccounts", JSON.parse(JSON.stringify(arrayOfUserAccounts)));
    });
    afterEach(() => {
      jest.restoreAllMocks();
      jest.clearAllMocks();
    });

    test("When the component is mounted, a User account is selected, and a user clicks reset, Then modal will default to no customer selected and will reset in Vuex", async () => {
      const commitSpy = jest.spyOn(store, "commit");
      store.commit("settings/setActiveUserIndex", 0);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });

      const expectedState = {
        entrykeyUser: "",
      };

      await wrapper.find("#input-dropdown-widget-user-account-").setValue("User account -2");

      const resetBtn = wrapper.find(".span__settings-tool-tip-reset-btn-txt-enable");
      expect(resetBtn.isVisible()).toBe(true);
      await resetBtn.trigger("click");

      expect(wrapper.vm.entrykeyUser).toBe(expectedState.entrykeyUser);
      expect(commitSpy).toHaveBeenCalledTimes(2);
    });
    test("Given that a customer account is selected in Vuex, When the method handling the 'cancel-id' customer event is invoked, Then the Vuex Store account data or selected customer account index is not modified", async () => {
      await store.commit("settings/setActiveUserIndex", 1);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });

      wrapper.vm.cancelUserUpdate();
      expect(store.state.settings.userAccounts).toStrictEqual(arrayOfUserAccounts);
      expect(store.state.settings.activeUserIndex).toStrictEqual(1); // this is the real data due to savechanges function Vuex stored data of activeUserIndex
    });

    test("When a user wants to save customer credentials and there is an error sending request, Then the modal will not not close and the modal will reset to make user re-input creds", async () => {
      await store.commit("settings/setActiveUserIndex", 1);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      jest.spyOn(store, "dispatch").mockImplementation(() => {
        return 401;
      });
      const editCustModal = wrapper.find(".div__edituser-form-controls");
      const saveChanges = wrapper.find(".span__settings-tool-tip-save-btn-txt-enable");
      await saveChanges.trigger("click");

      expect(wrapper.vm.openForInvalidCreds).toBe(true);
      expect(editCustModal).toBeTruthy();
    });
    test("When a user wants to save customer credentials and the request is returned with invalid credentials, Then the the edit-user modal will open with openForInvalidCreds set to true", async () => {
      await store.commit("settings/setActiveUserIndex", 1);
      const resetSpy = jest.spyOn(ComponentToTest.methods, "resetChanges");

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      jest.spyOn(store, "dispatch").mockImplementation(() => {
        return {
          status: 400,
        };
      });

      const saveChanges = wrapper.find(".span__settings-tool-tip-save-btn-txt-enable");
      await saveChanges.trigger("click");

      expect(resetSpy).toHaveBeenCalledTimes(1);
    });
    test("When a user wants to save customer credentials and there is no error sending request, Then the modal will close", async () => {
      await store.commit("settings/setActiveUserIndex", 1);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });

      jest.spyOn(store, "dispatch").mockImplementation(() => {
        return 200;
      });

      const saveChanges = wrapper.find(".span__settings-tool-tip-save-btn-txt-enable");
      await saveChanges.trigger("click");
      const closeEvent = wrapper.emitted("close-modal");
      expect(closeEvent[0]).toStrictEqual([true]);
    });

    test("Given a customer and user account selected in Vuex and the textbox for Customer Account is changed to an account different than the one in Vuex and a user account is selected in thet textbox, When the Save Changes button is clicked, Then the selected indices in Vuex for Customer and User accounts are updated to reflect the chosen options in the textboxes", async () => {
      jest.spyOn(socket, "send").mockImplementation(() => {});

      store.commit("settings/setActiveUserIndex", 0);
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });

      await wrapper.find("#input-dropdown-widget-user-account-").setValue("User account -2");
      await wrapper.vm.$nextTick(); // wait for update

      const saveChanges = wrapper.find(".span__settings-tool-tip-save-btn-txt-enable");
      await saveChanges.trigger("click");

      expect(store.state.settings.activeUserIndex).toStrictEqual(1); // this is the real data due to savechanges function Vuex stored data of activeUserIndex
    });
  });
  test("Given that no data are in the Vuex store, When the component is mounted, Then verify that Input of Customer ID and User ID are <empty>", () => {
    wrapper = mount(ComponentToTest, {
      store,
      localVue,
    });
    expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual("");
  });
  test("Given that badly formed data with missing userIds are in the Vuex store, When the component is mounted, Then verify that Input of Customer ID and User ID are <empty>", () => {
    store.commit("settings/setUserAccounts", arrayOfUserAccountsMissingUserIds);
    wrapper = mount(ComponentToTest, {
      store,
      localVue,
    });
    expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual("");
  });
  test("Given that badly formed data with empty customer account userName with missing userIds in the Vuex, When the component is mounted, Then verify that Input of Customer ID and User ID are <empty>", async () => {
    store.commit("settings/setUserAccounts", arrayOfCustomeridNullMissingUserIds);
    store.commit("settings/setActiveUserIndex", 0);
    wrapper = mount(ComponentToTest, {
      store,
      localVue,
    });

    expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual("");
  });
});
