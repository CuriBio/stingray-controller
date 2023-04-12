import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/settings/AddUser.vue";
import { AddUser as DistComponentToTest } from "@/dist/stingray.common";

import Vue from "vue";
import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import BootstrapVue from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.min.css";
import uuid from "@tofandel/uuid-base62";
import { TextValidation } from "@/js-utils/TextValidation.js";
let wrapper = null;

const localVue = createLocalVue();
localVue.use(BootstrapVue);
localVue.use(uuid);
localVue.use(Vuex);
let NuxtStore;
let store;

describe("AddUser", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  describe("AddUser.vue", () => {
    test("When mounting AddUser, Then it loads successfully and the `Add Customer` defined title text is rendered", () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const targetSpan = wrapper.find(".span__addUser-form-controls-content-title");
      expect(targetSpan.text()).toBe("Add New User");
    });
    test("Given there is a stored customer ID, When mounting AddUser, Then the customer ID input is automatically populated with that value and validated", () => {
      const storedCustomerId = "testId";
      store.commit("settings/setStoredAccounts", { customerId: storedCustomerId, usernames: [] });

      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
      const targetInput = wrapper.find("#input-widget-field-customer-id");
      expect(targetInput.element.value).toStrictEqual(storedCustomerId);
      const errorText = wrapper.find("#input-widget-feedback-customer-id");
      expect(errorText.text()).toStrictEqual("");
    });
  });

  describe("AddUser.enterUuidbase57", () => {
    beforeEach(async () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
    });
    afterEach(() => {
      wrapper.destroy();
      jest.restoreAllMocks();
    });

    test.each([
      ["06ad547f-fe02-477b-9473-f7977e4d5e14k", "ID", "customer-id", "validateUserAccountInput"],
      ["Cat lab;", "ID", "customer-id", "validateUserAccountInput"],
      ["Experiment anemia -1", "ID", "customer-id", "validateUserAccountInput"],
      ["Cat * lab", "password", "password-id", "validateUserAccountInput"],
      ["Valid", "password", "password-id", "validateUserAccountInput"],
      ["Cat lab", "password", "password-id", "validateUserAccountInput"],
    ])(
      "When the text %s (%s) is entered into the field found with the selector ID %s, Then the correct text validation function (%s) is called and the error message from the validation function is rendered below the input in the DOM",
      async (entry, testId, selectorIdSuffix, TextValidationType) => {
        const spiedTextValidator = jest.spyOn(TextValidation.prototype, TextValidationType);
        const targetInputField = wrapper.find("#input-widget-field-" + selectorIdSuffix);
        const targetErrorMessage = wrapper.find("#input-widget-feedback-" + selectorIdSuffix);

        targetInputField.setValue(entry);
        await Vue.nextTick();

        expect(spiedTextValidator).toHaveBeenCalledWith(entry, testId);
        expect(targetErrorMessage.text()).toStrictEqual(spiedTextValidator.mock.results[0].value);
      }
    );

    test.each([
      ["Experiment anemia alpha cells -1", "username", "validateUserAccountInput"],
      ["C", "username", "validateUserAccountInput"],
    ])(
      "When the text %s (%s) is entered into the field found with the selector ID username, Then the correct text validation function (%s) is called and the error message from the validation function is rendered below the input in the DOM",
      async (entry, testId, TextValidationType) => {
        const spiedTextValidator = jest.spyOn(TextValidation.prototype, TextValidationType);
        const targetInputField = wrapper.find("#input-dropdown-widget-username");
        const targetErrorMessage = wrapper.find("#input-dropdown-widget-feedback-username");

        targetInputField.setValue(entry);
        await Vue.nextTick();

        expect(spiedTextValidator).toHaveBeenCalledWith(entry, testId);
        expect(targetErrorMessage.text()).toStrictEqual(spiedTextValidator.mock.results[0].value);
      }
    );

    test.each([
      ["customer-id", "This field is required"],
      ["password-id", "This field is required"],
    ])(
      "Given some nonsense value in the input field with the DOM Id suffix %s, When the input field is updated to be a blank value, Then the error message below the text in the DOM matches what the business logic dictates (%s)",
      async (selectorIdSuffix, expectedMessage) => {
        const targetInputField = wrapper.find("#input-widget-field-" + selectorIdSuffix);
        const targetErrorMessage = wrapper.find("#input-widget-feedback-" + selectorIdSuffix);

        targetInputField.setValue("blah");
        await Vue.nextTick();
        // confirm that the pre-condition is different
        expect(targetErrorMessage.text()).not.toStrictEqual(expectedMessage);

        targetInputField.setValue("");
        await Vue.nextTick();
        expect(targetErrorMessage.text()).toStrictEqual(expectedMessage);
      }
    );

    test("Given some nonsense value in the input dropdown widget with the DOM Id suffix username, When the input field is updated to be a blank value, Then the error message below the text in the DOM matches what the business logic dictates 'This field is required'", async () => {
      const selectorIdSuffixUserName = "username";
      const targetInputField = wrapper.find("#input-dropdown-widget-" + selectorIdSuffixUserName);
      const targetErrorMessage = wrapper.find("#input-dropdown-widget-feedback-" + selectorIdSuffixUserName);
      await targetInputField.setValue("blah");
      await Vue.nextTick();

      // confirm that the pre-condition is different
      expect(targetErrorMessage.text()).not.toStrictEqual("This field is required");

      await targetInputField.setValue("");
      await Vue.nextTick();

      expect(targetErrorMessage.text()).toStrictEqual("This field is required");
    });
  });

  describe("AddUser.enableSaveButton", () => {
    beforeEach(async () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
    });

    afterEach(() => wrapper.destroy());
    test.each([
      ["0VSckkBYH2An3dqHEyfRRE", "06ad547f", "Experiment anemia -1", "color: rgb(255, 255, 255);"],
      [
        "5FY8KwTsQaUJ2KzHJGetfE123456asdfghDDDedsD74r",
        "06ad547f",
        "Experiment anemia -1 ",
        "color: rgb(63, 63, 63);",
      ],
      ["5FY8KwTsQaUJ2KzH*%#@JGetfE", "06ad547f", "Cat * lab", "color: rgb(63, 63, 63);"],
      ["fasd44", "06ad54", "Experiment anemia -1", "color: rgb(255, 255, 255);"],
      ["", "", "Experiment anemia -1", "color: rgb(63, 63, 63);"],
    ])(
      "Given an UUID (%s), pass Key (%s), username (%s) for 'Add Customer' as input, When the input contains based on valid the critera or failure, Then display of Label 'Save ID' is visible or greyed (%s)",
      async (uuid, password, username, saveBtnCss) => {
        const selectorIdSuffixAlphanumericId = "customer-id";
        const selectorIdSuffixpasswordId = "password-id";
        const selectorIdSuffixUserName = "username";

        const targetInputFieldUuid = wrapper.find("#input-widget-field-" + selectorIdSuffixAlphanumericId);
        targetInputFieldUuid.setValue(uuid);
        await Vue.nextTick();

        const targetInputFieldpassword = wrapper.find("#input-widget-field-" + selectorIdSuffixpasswordId);
        targetInputFieldpassword.setValue(password);
        await Vue.nextTick();

        const targetInputFieldUserName = wrapper.find("#input-dropdown-widget-" + selectorIdSuffixUserName);
        targetInputFieldUserName.setValue(username);
        await Vue.nextTick();

        const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
        const cancelBtn = targetButtonLabelBtn.at(0);
        expect(cancelBtn.attributes().style).toContain("color: rgb(255, 255, 255);");
        const saveBtn = targetButtonLabelBtn.at(1);
        expect(saveBtn.attributes().style).toContain(saveBtnCss);
      }
    );
  });

  describe("AddUser.clickedButton", () => {
    beforeEach(async () => {
      wrapper = mount(ComponentToTest, {
        store,
        localVue,
      });
    });
    afterEach(() => wrapper.destroy());

    test.each([["5FY8KwTsQa", "06ad547f", "Experiment anemia -1", "", "", "", "color: rgb(255, 255, 255);"]])(
      "Given an UUID(%s) , pass Key(%s), username(%s) for 'Add Customer' as input, When the input contains based on valid the critera or failure %s %s %s, Then display of Label 'Save ID' is visible %s, click on Cancel, an event 'cancel-id' is emmited to the parent and click on Save an event 'save-id' is emmited to parent with object containing uuid,password and username",
      async (
        uuidTest,
        passwordTest,
        usernameTest,
        invalidpassword,
        invalidUuid,
        invalidUserName,
        saveBtnCss
      ) => {
        const selectorIdSuffixAlphanumericId = "customer-id";
        const selectorIdSuffixpasswordId = "password-id";
        const selectorIdSuffixUserName = "username";

        const targetInputFieldUuid = wrapper.find("#input-widget-field-" + selectorIdSuffixAlphanumericId);
        const targetErrorMessageUuid = wrapper.find(
          "#input-widget-feedback-" + selectorIdSuffixAlphanumericId
        );
        targetInputFieldUuid.setValue(uuidTest);
        await Vue.nextTick();
        expect(targetErrorMessageUuid.text()).toStrictEqual(invalidUuid);
        const targetInputFieldpassword = wrapper.find("#input-widget-field-" + selectorIdSuffixpasswordId);
        const targetErrorMessagepassword = wrapper.find(
          "#input-widget-feedback-" + selectorIdSuffixpasswordId
        );
        targetInputFieldpassword.setValue(passwordTest);
        await Vue.nextTick();
        expect(targetErrorMessagepassword.text()).toStrictEqual(invalidpassword);
        const targetInputFieldUserName = wrapper.find("#input-dropdown-widget-" + selectorIdSuffixUserName);
        const targetErrorMessageUserName = wrapper.find(
          "#input-dropdown-widget-feedback-" + selectorIdSuffixUserName
        );
        targetInputFieldUserName.setValue(usernameTest);
        await Vue.nextTick();
        expect(targetErrorMessageUserName.text()).toStrictEqual(invalidUserName);
        const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
        const cancelBtn = targetButtonLabelBtn.at(0);
        expect(cancelBtn.attributes().style).toContain("color: rgb(255, 255, 255);");
        const saveBtn = targetButtonLabelBtn.at(1);
        expect(saveBtn.attributes().style).toContain(saveBtnCss);
        await cancelBtn.trigger("click");
        await Vue.nextTick();
        const cancelIdEvents = wrapper.emitted("cancel-id");
        expect(cancelIdEvents).toHaveLength(1);
        expect(cancelIdEvents[0]).toStrictEqual([]);
        await saveBtn.trigger("click");
        await Vue.nextTick();
        const saveIdEvents = wrapper.emitted("save-id");
        expect(saveIdEvents).toHaveLength(1);
        expect(saveIdEvents[0]).toStrictEqual([
          {
            userPassword: passwordTest,
            username: usernameTest,
            customerId: uuidTest,
          },
        ]);
      }
    );
  });
});
