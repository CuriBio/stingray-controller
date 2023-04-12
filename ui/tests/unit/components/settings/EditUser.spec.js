import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/settings/EditUser.vue";
import { EditUser as DistComponentToTest } from "@/dist/stingray.common";

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

describe("EditUser", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  describe("EditUser.vue", () => {
    const editcustomer = {
      uuid: "",
      password: "",
      username: "",
    };
    const propsData = {
      dialogdata: editcustomer,
    };
    beforeEach(async () => {
      wrapper = mount(ComponentToTest, {
        store,
        propsData,
        localVue,
      });
    });
    afterEach(() => wrapper.destroy());
    test("When mounting EditUser from the build dist file, Then it loads successfully and the `Edit Customer` defined title text is rendered", () => {
      wrapper = mount(DistComponentToTest, {
        store,
        propsData,
        localVue,
      });
      const targetSpan = wrapper.find(".span__edituser-form-controls-content-title");
      expect(targetSpan.text()).toStrictEqual("Edit User Credentials");
    });
  });

  describe("EditUser.invalidCreds", () => {
    const propsData = {
      openForInvalidCreds: true,
      dialogdata: {
        customerId: "testId",
        password: "testPass",
        username: "testUserName",
      },
    };
    beforeEach(async () => {
      wrapper = mount(ComponentToTest, {
        store,
        propsData,
        localVue,
      });
    });
    afterEach(() => wrapper.destroy());
    test("When mounting EditUser with invalid credentials, Then it loads with 'Invalid Customer ID, Username, or Password' text", () => {
      const idErrorMessage = wrapper.find("#input-widget-feedback-customer-id");
      const passErrorMessage = wrapper.find("#input-widget-feedback-password-id");
      const usernameErrorMessage = wrapper.find("#input-widget-feedback-username");

      const invalidText = "Invalid Customer ID, Username, or Password";

      expect(idErrorMessage.text()).toStrictEqual(invalidText);
      expect(passErrorMessage.text()).toStrictEqual(invalidText);
      expect(usernameErrorMessage.text()).toStrictEqual(invalidText);
    });
    test.each(["password-id", "customer-id", "username"])(
      "When EditUser has invalid credentials, Then both ID and password will mount with invalid text and will both become become valid with any change to %s",
      async (selectorIdSuffix) => {
        const idErrorMessage = wrapper.find("#input-widget-feedback-customer-id");
        const passErrorMessage = wrapper.find("#input-widget-feedback-password-id");
        const usernameErrorMessage = wrapper.find("#input-widget-feedback-username");
        const invalidText = "Invalid Customer ID, Username, or Password";

        expect(idErrorMessage.text()).toStrictEqual(invalidText);
        expect(passErrorMessage.text()).toStrictEqual(invalidText);
        expect(usernameErrorMessage.text()).toStrictEqual(invalidText);

        const targetInputField = wrapper.find("#input-widget-field-" + selectorIdSuffix);
        await targetInputField.setValue("new entry");
        await wrapper.vm.$nextTick(); // wait for update

        expect(idErrorMessage.text()).toStrictEqual("");
        expect(passErrorMessage.text()).toStrictEqual("");
        expect(usernameErrorMessage.text()).toStrictEqual("");
      }
    );
  });
  describe("EditUser.enterUuidbase57", () => {
    const editcustomer = {
      uuid: "",
      password: "",
      username: "",
    };
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
      ["Experiment anemia alpha cells -1", "username", "username", "validateUserAccountInput"],
      ["C", "username", "username", "validateUserAccountInput"],
      ["", "username", "username", "validateUserAccountInput"],
    ])(
      "When the text %s (%s) is entered into the field found with the selector ID %s, Then the correct text validation function (%s) is called and the error message from the validation function is rendered below the input in the DOM",
      async (entry, textId, selectorIdSuffix, TextValidationType) => {
        if (selectorIdSuffix === "customer-id") {
          editcustomer.customerId = entry;
        }
        if (selectorIdSuffix === "password-id") {
          editcustomer.password = entry;
        }
        if (selectorIdSuffix === "username") {
          editcustomer.username = entry;
        }

        const propsData = {
          dialogdata: editcustomer,
        };
        wrapper = mount(ComponentToTest, {
          store,
          propsData,
          localVue,
        });

        const spiedTextValidator = jest.spyOn(TextValidation.prototype, TextValidationType);

        const targetInputField = wrapper.find("#input-widget-field-" + selectorIdSuffix);

        const targetErrorMessage = wrapper.find("#input-widget-feedback-" + selectorIdSuffix);

        targetInputField.setValue(entry);

        await wrapper.vm.$nextTick();
        expect(spiedTextValidator).toHaveBeenCalledWith(entry, textId);

        expect(targetErrorMessage.text()).toStrictEqual(spiedTextValidator.mock.results[0].value);
      }
    );

    test.each([
      ["customer-id", "This field is required"],
      ["password-id", "This field is required"],
      ["username", "This field is required"],
    ])(
      "Given some nonsense value in the input field with the DOM Id suffix %s, When the input field is updated to be a blank value, Then the error message below the text in the DOM matches what the business logic dictates (%s)",
      async (selectorIdSuffix, expectedMessage) => {
        const propsData = {
          dialogdata: editcustomer,
        };
        wrapper = mount(ComponentToTest, {
          store,
          propsData,
          localVue,
        });

        const targetInputField = wrapper.find("#input-widget-field-" + selectorIdSuffix);
        const targetErrorMessage = wrapper.find("#input-widget-feedback-" + selectorIdSuffix);
        targetInputField.setValue("blah");
        await wrapper.vm.$nextTick();
        // confirm that the pre-condition is different
        expect(targetErrorMessage.text()).not.toStrictEqual(expectedMessage);

        targetInputField.setValue("");
        await wrapper.vm.$nextTick();

        expect(targetErrorMessage.text()).toStrictEqual(expectedMessage);
      }
    );
  });

  describe("EditUser.enableSaveButton", () => {
    const editcustomer = {
      uuid: "",
      password: "",
      username: "",
    };
    afterEach(() => wrapper.destroy());
    test.each([
      ["0VSckkBYH2An3dqHEyfRRE", "06ad547f", "Experiment anemia -1", "color: rgb(255, 255, 255);"],
      [
        "5FY8KwTsQaU-J2KzHJGetfE4k2DOd0233l-DlflkakCmfk-dq13",
        "06ad547f",
        "Experiment anemia -1",
        "color: rgb(63, 63, 63);",
      ],
      ["5FY8Kw#$%^*JGetfE", "06ad547f", "Cat * lab", "color: rgb(63, 63, 63);"],
      ["fasd44", "06ad54", "Experiment anemia -1", "color: rgb(255, 255, 255);"],
      ["", "", "Experiment anemia -1", "color: rgb(63, 63, 63);"],
    ])(
      "Given an UUID (%s), pass Key (%s), username (%s) for 'Edit Customer' as input, When the input contains based on valid the critera or failure, Then display of Label 'Save ID' is visible or greyed (%s)",
      async (uuid, password, username, saveBtnCss) => {
        const selectorIdSuffixAlphanumericId = "customer-id";
        const selectorIdSuffixpasswordId = "password-id";
        const selectorIdSuffixUserName = "username";

        editcustomer.uuid = uuid;
        editcustomer.password = password;
        editcustomer.username = username;

        const propsData = {
          dialogdata: editcustomer,
        };
        wrapper = mount(ComponentToTest, {
          store,
          propsData,
          localVue,
        });

        const targetInputFieldUuid = wrapper.find("#input-widget-field-" + selectorIdSuffixAlphanumericId);
        targetInputFieldUuid.setValue(uuid);
        await wrapper.vm.$nextTick();
        const targetInputFieldpassword = wrapper.find("#input-widget-field-" + selectorIdSuffixpasswordId);
        targetInputFieldpassword.setValue(password);
        await wrapper.vm.$nextTick();

        const targetInputFieldUserName = wrapper.find("#input-widget-field-" + selectorIdSuffixUserName);
        targetInputFieldUserName.setValue(username);
        await wrapper.vm.$nextTick();

        const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
        const cancelBtn = targetButtonLabelBtn.at(0);
        expect(cancelBtn.attributes().style).toContain("color: rgb(255, 255, 255);");
        const deleteBtn = targetButtonLabelBtn.at(1);
        expect(deleteBtn.attributes().style).toContain("color: rgb(255, 255, 255);");
        const saveBtn = targetButtonLabelBtn.at(2);
        expect(saveBtn.attributes().style).toContain(saveBtnCss);
      }
    );
  });

  describe("EditUser.clickedButton", () => {
    const editcustomer = {
      customerId: "",
      password: "",
      username: "",
    };
    afterEach(() => wrapper.destroy());
    test.each([
      [
        "5FY8KwTsQaUJ2KzHJ",
        "06ad547f-fe02",
        "Experiment anemia -1",
        "",
        "",
        "",
        "color: rgb(255, 255, 255);",
      ],
    ])(
      "Given an UUID(%s) , pass Key(%s), username(%s) for 'Edit Customer' as input, When the input contains based on valid the critera or failure %s %s %s, Then display of Label 'Save ID' is visible %s, click on Cancel, an event 'cancel-id' is emmited to the parent, click on Delete an event 'delete-id' is emmited to the parent, and click on Save an event 'save-id' is emmited to parent",
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

        editcustomer.customerId = uuidTest;
        editcustomer.password = passwordTest;
        editcustomer.username = usernameTest;

        const propsData = {
          dialogdata: editcustomer,
        };
        wrapper = mount(ComponentToTest, {
          store,
          propsData,
          localVue,
        });

        const targetInputFieldUuid = wrapper.find("#input-widget-field-" + selectorIdSuffixAlphanumericId);
        const targetErrorMessageUuid = wrapper.find(
          "#input-widget-feedback-" + selectorIdSuffixAlphanumericId
        );
        targetInputFieldUuid.setValue(uuidTest);
        await wrapper.vm.$nextTick();

        expect(targetErrorMessageUuid.text()).toStrictEqual(invalidUuid);

        const targetInputFieldpassword = wrapper.find("#input-widget-field-" + selectorIdSuffixpasswordId);
        const targetErrorMessagepassword = wrapper.find(
          "#input-widget-feedback-" + selectorIdSuffixpasswordId
        );
        targetInputFieldpassword.setValue(passwordTest);
        await wrapper.vm.$nextTick();

        expect(targetErrorMessagepassword.text()).toStrictEqual(invalidpassword);

        const targetInputFieldUserName = wrapper.find("#input-widget-field-" + selectorIdSuffixUserName);
        const targetErrorMessageUserName = wrapper.find("#input-widget-feedback-" + selectorIdSuffixUserName);
        targetInputFieldUserName.setValue(usernameTest);
        await wrapper.vm.$nextTick();

        expect(targetErrorMessageUserName.text()).toStrictEqual(invalidUserName);

        const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
        const cancelBtn = targetButtonLabelBtn.at(0);
        expect(cancelBtn.attributes().style).toContain("color: rgb(255, 255, 255);");
        const deleteBtn = targetButtonLabelBtn.at(1);
        expect(deleteBtn.attributes().style).toContain("color: rgb(255, 255, 255);");
        const saveBtn = targetButtonLabelBtn.at(2);
        expect(saveBtn.attributes().style).toContain(saveBtnCss);

        await cancelBtn.trigger("click");
        await wrapper.vm.$nextTick();
        const cancelIdEvents = wrapper.emitted("cancel-id");
        expect(cancelIdEvents).toHaveLength(1);
        expect(cancelIdEvents[0]).toStrictEqual([]);

        await deleteBtn.trigger("click");
        await wrapper.vm.$nextTick();

        const deleteIdEvents = wrapper.emitted("delete-id");
        expect(deleteIdEvents).toHaveLength(1);

        await saveBtn.trigger("click");
        await wrapper.vm.$nextTick();

        const saveIdEvents = wrapper.emitted("save-id");
        expect(saveIdEvents).toHaveLength(1);
        expect(saveIdEvents[0]).toStrictEqual([
          {
            customerId: uuidTest,
            userPassword: passwordTest,
            username: usernameTest,
          },
        ]);
      }
    );
  });
});
