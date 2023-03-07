import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/basic-widgets/InputDropDown.vue";
import { InputDropDown as DistComponentToTest } from "@/dist/stingray.common";
import { shallowMount } from "@vue/test-utils";
import SmallDropDown from "@/components/basic-widgets/SmallDropDown.vue";
import SelectDropDown from "@/components/basic-widgets/SelectDropDown.vue";

import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import BootstrapVue from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.min.css";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(BootstrapVue);

let NuxtStore;
let store;

describe("InputDropDown.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => wrapper.destroy());
  const nicknames = ["Customer Account 1", "Customer Account 2", "Customer Account 3"];
  test("When mounting InputDropDown from the build dist file, Then it loads successfully and the props defined title is rendered", () => {
    const propsData = {
      titleLabel: "Customer ID",
      optionsText: nicknames,
    };
    wrapper = shallowMount(DistComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetSpan = wrapper.find(".span__input-dropdown-content-label");

    expect(targetSpan.text()).toStrictEqual("Customer ID");
  });
  test("When the InputDropDown is mounted, Then it loads successfully and the props defined placeholder is rendered on input field", () => {
    const propsData = {
      titleLabel: "Customer ID",
      optionsText: nicknames,
      placeholder: "Select Customer ID",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetInput = wrapper.find("#input-dropdown-widget-");
    expect(targetInput.attributes().placeholder).toStrictEqual("Select Customer ID");
  });
  test("When the user types a valid option from the list, Then an event 'update' is emitted with the entered text", async () => {
    const propsData = {
      titleLabel: "Customer ID",
      optionsText: nicknames,
      placeholder: "Select Customer ID",
      value: "",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const customer = "Customer Account 1"; // new Customer
    const inputWidget = wrapper.find("#input-dropdown-widget-");
    inputWidget.element.value = customer;
    await inputWidget.trigger("input");
    const parentIdEvents = wrapper.emitted("update:value");
    expect(parentIdEvents).toHaveLength(1);
    expect(parentIdEvents).toStrictEqual([[customer]]);
  });
  test("When the InputDropDown is mounted, Then a prop messageIfInvalid is set to true and invalidText is provided as value is <empty>, an error text is rendered", async () => {
    const propsData = {
      titleLabel: "Customer ID",
      optionsText: nicknames,
      placeholder: "Select Customer ID",
      value: "",
      invalidText: "This field is required",
      messageIfInvalid: true,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetDiv = wrapper.find(".div__input-dropdown-controls-content-feedback");
    const targetDropdownSurrondedBox = wrapper.find(".div__input-dropdown-controls-content-widget--invalid");
    expect(targetDropdownSurrondedBox.isVisible()).toBe(true);
    expect(targetDiv.text()).toStrictEqual("This field is required");
  });
  test("Given the disabled prop is set to true, When the user types a few characters, Then no update event is emitted by the component.", async () => {
    const propsData = {
      titleLabel: "Customer ID",
      optionsText: nicknames,
      placeholder: "Select Customer ID",
      value: "",
      invalidText: "This field is required",
      messageIfInvalid: true,
      disabled: true,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const userdata = "Demo Account"; // some data
    const inputWidget = wrapper.find("#input-dropdown-widget-");
    expect(inputWidget.html()).toContain("disabled");
    inputWidget.element.value = userdata;
    await inputWidget.trigger("input");
    const parentIdEvents = wrapper.emitted("update:value");
    expect(parentIdEvents).toBeUndefined();
  });
  test("When the InputDropDown is mounted, Then the widget width is modified in props to that of the value set from the props value 'entryWidth'", async () => {
    const propsData = {
      titleLabel: "Customer ID",
      optionsText: nicknames,
      placeholder: "Select Customer ID",
      value: "",
      invalidText: "This field is required",
      messageIfInvalid: true,
      disabled: true,
      inputWidth: 390,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const background = wrapper.find(".div__input-dropdown-background");
    expect(background.attributes("style")).toStrictEqual(
      "width: 394px; height: 100px; background: rgb(0, 0, 0); border: 2px solid rgb(0, 0, 0);"
    );
    const inputTitleLabel = wrapper.find(".span__input-dropdown-content-label");
    expect(inputTitleLabel.attributes("style")).toStrictEqual("width: 390px;");
    const inputBoundedDiv = wrapper.find(".div__input-dropdown-controls-content-widget");
    expect(inputBoundedDiv.attributes("style")).toStrictEqual("width: 390px; top: 40px;");
    const inputTextEntrySpan = wrapper.find(".span__input-dropdown-controls-content-input-txt-widget");
    expect(inputTextEntrySpan.attributes("style")).toStrictEqual("width: 390px;");
    const inputTextEntryFeedback = wrapper.find(".div__input-dropdown-controls-content-feedback");
    expect(inputTextEntryFeedback.attributes("style")).toStrictEqual("width: 390px; top: 88px;");
  });
  test("When the InputDropDown is mounted with the title prop empty/blank, Then height of the widget is modified  in the event of title being empty without a hole", async () => {
    const propsData = {
      titleLabel: "",
      optionsText: nicknames,
      placeholder: "Select Customer ID",
      value: "",
      invalidText: "This field is required",
      messageIfInvalid: true,
      disabled: true,
      inputWidth: 390,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const background = wrapper.find(".div__input-dropdown-background");
    expect(background.attributes("style")).toStrictEqual(
      "width: 394px; height: 60px; background: rgb(0, 0, 0); border: 2px solid rgb(0, 0, 0);"
    );
    const inputTitleLabel = wrapper.find(".span__input-dropdown-content-label");
    expect(inputTitleLabel.exists()).toBe(false);

    const inputBoundedDiv = wrapper.find(".div__input-dropdown-controls-content-widget");
    expect(inputBoundedDiv.attributes("style")).toStrictEqual("width: 390px; top: 0px;");
    const inputTextEntrySpan = wrapper.find(".span__input-dropdown-controls-content-input-txt-widget");
    expect(inputTextEntrySpan.attributes("style")).toStrictEqual("width: 390px;");
    const inputTextEntryFeedback = wrapper.find(".div__input-dropdown-controls-content-feedback");
    expect(inputTextEntryFeedback.attributes("style")).toStrictEqual("width: 390px; top: 48px;");
  });
  describe("SmallDropdown.vue", () => {
    test("When the disableToggle prop changes to true , Then the options list will not expand when a user clicks on it", async () => {
      const toggleSpy = jest.spyOn(SmallDropDown.methods, "toggle");
      const wrapper = mount(SmallDropDown, {
        store,
        localVue,
        propsData: {
          optionsText: ["option1", "option2"],
          disableToggle: false,
        },
      });

      await wrapper.setProps({ disableToggle: true });
      const selectedOpt = wrapper.find(".span__small-dropdown-controls-content-input-txt-widget");
      await wrapper.find(".div__small-dropdown-controls-content-widget").trigger("click");

      expect(wrapper.vm.visible).toBe(false);
      expect(selectedOpt.text()).toContain("option1");
      expect(toggleSpy).toHaveBeenCalledTimes(0);
    });
    test("When the disableSelection prop changes to true, Then the ability to change the selected option should be disabled", async () => {
      const toggleSpy = jest.spyOn(SmallDropDown.methods, "toggle");
      const changeSpy = jest.spyOn(SmallDropDown.methods, "changeSelection");
      const wrapper = mount(SmallDropDown, {
        store,
        localVue,
        propsData: {
          optionsText: ["option1", "option2"],
          disableSelection: false,
        },
      });

      await wrapper.setProps({ disableSelection: true });
      expect(wrapper.vm.visible).toBe(false);

      const selectedOpt = wrapper.find(".span__small-dropdown-controls-content-input-txt-widget");
      expect(selectedOpt.text()).toContain("option1");

      await wrapper.find(".div__small-dropdown-controls-content-widget").trigger("click");
      const listOpts = wrapper.findAll("li");

      expect(toggleSpy).toHaveBeenCalledTimes(1);
      expect(listOpts).toHaveLength(1);

      // try to select other option when disabled
      await listOpts.at(0).trigger("click");

      // selected option should not have changed
      expect(selectedOpt.text()).toContain("option1");
      expect(changeSpy).toHaveBeenCalledTimes(0);
    });
  });
});
