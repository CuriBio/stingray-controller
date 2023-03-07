import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/settings/SettingsForm.vue";
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
  /**
   * Returns an object of DOM span id's
   * @param {Object} wrap - Component reference
   * @return {Object} buttons - An Object
   */
  function getButtons(wrap) {
    const buttons = {
      addUserBtn: wrap.find(".span__settingsform-user-add-btn_txt"),
      editUserBtn: wrap.find(".span__settingsform-user-edit-btn-txt"),
    };
    return buttons;
  }
  /**
   * Returns an object of DOM span id's
   * @param {Object} wrap - Component reference
   * @return {Object} validButtons - An Object
   */
  function getSettingsButtonEnabled(wrap) {
    const validButtons = {
      resetBtn: wrap.find(".span__settings-tool-tip-reset-btn-txt-enable"),
      saveBtn: wrap.find(".span__settings-tool-tip-save-btn-txt-enable"),
      saveBtnContainer: wrap.find(".div__settings-tool-tip-save-btn-enable"),
      cancelBtn: wrap.find(".div__settings-tool-tip-cancel-btn"),
    };
    return validButtons;
  }
  /**
   * Returns an object of DOM span id's
   * @param {Object} wrap - Component reference
   * @return {Object} validButtons - An Object
   */
  function getSettingsButtonDisable(wrap) {
    const validButtons = {
      resetBtn: wrap.find(".span__settings-tool-tip-reset-btn-txt-disable"),
      saveBtn: wrap.find(".span__settings-tool-tip-save-btn-txt-disable"),
      saveBtnContainer: wrap.find(".div__settings-tool-tip-save-btn-disable"),
    };
    return validButtons;
  }
  /**
   * Returns an object of DOM div id's
   * @param {Object} wrap - Component reference
   * @return {Object} invalidBoxes - An Object
   */
  function getInvalidBoxes(wrap) {
    const boxes = wrap.findAll(".div__input-dropdown-controls-content-widget--invalid");
    const invalidBoxes = {
      customer: boxes.at(0),
      // user: boxes.at(1),
    };
    return invalidBoxes;
  }
  /**
   * Returns an object of DOM div id's
   * @param {Object} wrap - Component reference
   * @return {Object} validBoxes - An Object
   */
  function getValidBoxes(wrap) {
    const boxes = wrapper.findAll(".div__input-dropdown-controls-content-widget--valid");
    const validBoxes = {
      customer: boxes.at(0),
      // user: boxes.at(1),
    };
    return validBoxes;
  }
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => {
    wrapper.destroy();
  });
  describe("Given Vuex has a valid user account of 'User account -1' but no user index selected", () => {
    beforeEach(() => {
      // commit a deep copy of the template object to the Vuex store using JSON stringify/parse, as it may be modified during tests. https://www.javascripttutorial.net/object/3-ways-to-copy-objects-in-javascript/
      store.commit("settings/setUserAccounts", JSON.parse(JSON.stringify(arrayOfUserAccounts)));
    });
    describe("Given the component is mounted", () => {
      beforeEach(() => {
        wrapper = mount(ComponentToTest, {
          store,
          localVue,
        });
      });

      test("When the value of User is set to 'User account -1', Then the buttons 'Add New User', 'Edit ID' are enabled", async () => {
        await wrapper.find("#input-dropdown-widget-user-account-").setValue("User account -1");
        await wrapper.vm.$nextTick(); // wait for update

        const allButtons = getButtons(wrapper);
        await wrapper.vm.$nextTick(); // wait for update
        expect(allButtons.addUserBtn.isVisible()).toBe(true);
        expect(allButtons.editUserBtn.isVisible()).toBe(true);
      });
    });

    test("When the component is mounted, Then 'Add New User' is enabled and 'Edit ID' is disabled", async () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      await wrapper.vm.$nextTick(); // wait for update
      const allButtons = getButtons(wrapper);
      await wrapper.vm.$nextTick(); // wait for update
      expect(allButtons.addUserBtn.isVisible()).toBe(true);
      expect(allButtons.editUserBtn.isVisible()).toBe(false);
    });
    test("When the component is mounted, Then visually the Reset and Save Buttons are disabled", async () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });

      const settingsButtons = getSettingsButtonDisable(wrapper);
      expect(settingsButtons.resetBtn.isVisible()).toBe(true);
      expect(settingsButtons.saveBtn.isVisible()).toBe(true);
      expect(settingsButtons.saveBtnContainer.isVisible()).toBe(true);
    });
    test("Given the SettingsForm has a valid customer account set as 'User account -1', When the Vuex Store data specifies a valid Customer ID, Then visually the Reset and Save Buttons are enabled", async () => {
      store.commit("settings/setActiveUserIndex", 0);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const settingsButtons = getSettingsButtonEnabled(wrapper);
      expect(settingsButtons.resetBtn.isVisible()).toBe(true);
      expect(settingsButtons.saveBtn.isVisible()).toBe(true);
      expect(settingsButtons.saveBtnContainer.isVisible()).toBe(true);
    });
    test("Given the SettingsForm has Vuex data is an empty array, When the value Customer ID is <empty>, Then visually the RED Box is enabled around the Customer ID", async () => {
      const arrayOfEmptyUserAccounts = [];
      store.commit("settings/setUserAccounts", arrayOfEmptyUserAccounts);
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const invalidBox = getInvalidBoxes(wrapper);
      expect(invalidBox.customer.isVisible()).toBe(true);
    });
    test("Given the SettingsForm has a valid customer account set as 'User account -1', When the 'User account -1' is in focus, Then the GREEN Box is enabled around the Customer ID", async () => {
      store.commit("settings/setActiveUserIndex", 0);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const validBoxes = getValidBoxes(wrapper);
      expect(validBoxes.customer.isVisible()).toBe(true);
    });
    test("Given the SettingsForm has a valid customer account set as 'User account -1', When the user now modifies to non-existent customer say 'User account -', Then validate that Red Boxes are visible around Customer ID 'Add New Customer Button' is enabled", async () => {
      store.commit("settings/setActiveUserIndex", 0);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });

      const validBoxes = getValidBoxes(wrapper);
      expect(validBoxes.customer.isVisible()).toBe(true);

      await wrapper.find("#input-dropdown-widget-user-account-").setValue("User account -"); // customer with this doesn't exist.

      await wrapper.vm.$nextTick(); // wait for update

      const invalidBox = getInvalidBoxes(wrapper);
      expect(invalidBox.customer.isVisible()).toBe(true);
      const allButtons = getButtons(wrapper);
      await wrapper.vm.$nextTick(); // wait for update
      expect(allButtons.addUserBtn.isVisible()).toBe(true);
      expect(allButtons.editUserBtn.isVisible()).toBe(false);
    });

    test("Given the SettingsForm has a valid customer account set as 'User account -1', When the user sets the value on input with same default value 'User account -1' , Then validate that Green Box is around the input, and based on rules relevant buttons are enabled", async () => {
      store.commit("settings/setActiveUserIndex", 0);
      // store.commit("settings/setActiveUserIndex", 0);

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
        data() {
          return {
            disableEditUser: true,
          };
        },
      });

      await wrapper.vm.$nextTick(); // wait for update

      await wrapper.find("#input-dropdown-widget-user-account-").setValue("User account -1");
      await wrapper.vm.$nextTick(); // wait for update

      const validBoxes = getValidBoxes(wrapper);
      expect(validBoxes.customer.isVisible()).toBe(true);
      const allButtons = getButtons(wrapper);
      await wrapper.vm.$nextTick(); // wait for update
      expect(allButtons.addUserBtn.isVisible()).toBe(true);
      expect(allButtons.editUserBtn.isVisible()).toBe(true);
    });

    test("When the component is mounted and User account is/is not selected, Then the cancel button is visible and will close modal on click", async () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const settingsButtons = await getSettingsButtonEnabled(wrapper);

      expect(settingsButtons.cancelBtn.isVisible()).toBe(true);
      await settingsButtons.cancelBtn.trigger("click");

      const closeEvent = wrapper.emitted("close-modal");
      expect(closeEvent[0]).toStrictEqual([false]);
    });

    test("When the component is mounted and User account is/is not selected, Then clicking the save button will be disabled", async () => {
      const commitSpy = jest.spyOn(store, "commit");
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const settingsButtons = await getSettingsButtonDisable(wrapper);

      expect(settingsButtons.saveBtn.isVisible()).toBe(true);
      await settingsButtons.saveBtn.trigger("click");

      expect(commitSpy).toHaveBeenCalledTimes(0);
    });
  });
});
