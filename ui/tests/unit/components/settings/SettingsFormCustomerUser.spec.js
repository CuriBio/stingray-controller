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
  describe("Given Vuex has valid user but no user index", () => {
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
      describe("Given that the SettingsForm has been populated with a new User account through invoking the methods handling the 'save-id' event for Add User", () => {
        beforeEach(async () => {
          const addUser = {
            customerId: "5FY8KwTsQaUJ2KzHJGetfE",
            userPassword: "ba86b8f0-6fdf-4944-87a0-8a491a19490e",
            userName: "User account -3",
          };

          /* This testing is based on the inspiration provided by the documentation handbook mentioned in the link below */
          /* https://lmiller1990.github.io/vue-testing-handbook/testing-emitted-events.html#write-a-component-and-test   */
          wrapper.vm.saveNewUser(addUser);

          await wrapper.vm.$nextTick();
          // Eli (11/30/20): This beforeEach block of code will always get executed, and these expect statements help confirm the pre-condition to the test is set up correctly
          // eslint-disable-next-line jest/no-standalone-expect
          expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual(
            "User account -3"
          );
          // Eli (11/30/20): This beforeEach block of code will always get executed, and these expect statements help confirm the pre-condition to the test is set up correctly
          // eslint-disable-next-line jest/no-standalone-expect
          // expect(wrapper.find("#input-dropdown-widget-user-").element.value).toStrictEqual("");

          // Eli (11/30/20): This beforeEach block of code will always get executed, and these expect statements help confirm the pre-condition to the test is set up correctly
          // eslint-disable-next-line jest/no-standalone-expect
          expect(wrapper.find("#user-account-0").text()).toStrictEqual("User account -1");
          // Eli (11/30/20): This beforeEach block of code will always get executed, and these expect statements help confirm the pre-condition to the test is set up correctly
          // eslint-disable-next-line jest/no-standalone-expect
          expect(wrapper.find("#user-account-1").text()).toStrictEqual("User account -2");
          // Eli (11/30/20): This beforeEach block of code will always get executed, and these expect statements help confirm the pre-condition to the test is set up correctly
          // eslint-disable-next-line jest/no-standalone-expect
          expect(wrapper.find("#user-account-2").text()).toStrictEqual("User account -3");
        });
        test("When the method handling the 'save-id' event for the Edit User button is invoked to change the userName, Then the User ID dropdown list gets updated to change to the new userName", async () => {
          const activeUserIndex = 1;
          const editUser = JSON.parse(JSON.stringify(arrayOfUserAccounts[activeUserIndex]));

          await wrapper.find("#input-dropdown-widget-user-account-").setValue(editUser.userName);
          await wrapper.vm.$nextTick(); // wait for update

          editUser.userName = "Renamed Account -2";
          wrapper.vm.applyUserUpdate(editUser);

          await wrapper.vm.$nextTick();
          expect(wrapper.find("#user-account-0").text()).toStrictEqual("User account -1");
          expect(wrapper.find("#user-account-1").text()).toStrictEqual("Renamed Account -2");
          expect(wrapper.find("#user-account-2").text()).toStrictEqual("User account -3");
        });
        test("When the method handling the user event 'delete-id' is invoked, Then the selected user account is removed from the User dropdown", async () => {
          const activeUserIndex = 0;
          const deleteUser = JSON.parse(JSON.stringify(arrayOfUserAccounts[activeUserIndex]));

          await wrapper.find("#input-dropdown-widget-user-account-").setValue(deleteUser.userName);
          await wrapper.vm.$nextTick(); // wait for update

          wrapper.vm.deleteUser();
          await wrapper.vm.$nextTick();

          expect(wrapper.find("#user-account-0").text()).toStrictEqual("User account -2");
          expect(wrapper.find("#user-account-1").text()).toStrictEqual("User account -3");
        });
      });
      // });

      test("When the SettingsForm method that handles receiving the add user 'save-id' event is invoked with a new user account, Then the Username text input is updated with userName value of the newly added account", async () => {
        const addUser = {
          customerId: "5FY8KwTsQaUJ2KzHJGetfE",
          userPassword: "ba86b8f0-6fdf-4944-87a0-8a491a19490e",
          userName: "User account -3",
        };
        /* This testing is based on the inspiration provided by the documentation handbook mentioned in the link below */
        /* https://lmiller1990.github.io/vue-testing-handbook/testing-emitted-events.html#write-a-component-and-test   */
        wrapper.vm.saveNewUser(addUser);

        await wrapper.vm.$nextTick();
        expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual(
          "User account -3"
        );
        // expect(wrapper.find("#input-dropdown-widget-user-").element.value).toStrictEqual("");
      });
    });
    describe("Given a valid user is selected in Vuex and the component is mounted", () => {
      beforeEach(() => {
        store.commit("settings/setActiveUserIndex", 0);
        wrapper = mount(ComponentToTest, {
          store,
          localVue,
        });
      });
      test("When the SettingsForm method that handles receiving the 'cancel-id' event is invoked, Then the Username text input does not change", async () => {
        expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual(
          "User account -1"
        );
        /* This testing is based on the inspiration provided by the documentation handbook mentioned in the link below */
        /* https://lmiller1990.github.io/vue-testing-handbook/testing-emitted-events.html#write-a-component-and-test   */
        wrapper.vm.cancelUserUpdate();

        expect(wrapper.find("#input-dropdown-widget-user-account-").element.value).toStrictEqual(
          "User account -1"
        );
      });
    });
  });
});
