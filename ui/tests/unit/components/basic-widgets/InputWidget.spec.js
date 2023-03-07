import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/basic-widgets/InputWidget.vue";
import { InputWidget as DistComponentToTest } from "@/dist/mantarray.common";

import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import BootstrapVue from "bootstrap-vue";
import "bootstrap/dist/css/bootstrap.min.css";
import uuid from "@tofandel/uuid-base62";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(BootstrapVue);
localVue.use(uuid);

let NuxtStore;
let store;

describe("InputWidget.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => wrapper.destroy());
  test("When mounting from the built dist file, Then it loads successfully and the props defined title is rendered", () => {
    const propsData = {
      titleLabel: "Enter  Alphanumeric  ID",
    };
    wrapper = mount(DistComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetSpan = wrapper.find(".span__input-content-label");

    expect(targetSpan.text()).toStrictEqual("Enter  Alphanumeric  ID"); // the value of &nbsp<wbr> is '\u00a0'
  });
  test("When the Component is mounted, Then it loads successfully and the props defined placeholder is rendered on input field", () => {
    const propsData = {
      titleLabel: "Enter  Alphanumeric  ID",
      placeholder: "place holder",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetInput = wrapper.find("#input-widget-field-");
    expect(targetInput.attributes().placeholder).toStrictEqual("place holder");
  });
  test("When the Component is mounted with an initial value supplied as a prop, Then the input field is populated with that value", () => {
    const expected = "quick brown fox";
    const propsData = {
      initialValue: expected,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetInput = wrapper.find("#input-widget-field-");
    expect(targetInput.element.value).toStrictEqual(expected);
  });
  test("When the Component is mounted with a DOM ID suffix supplied as a prop, Then the input field and feedback text have that included in their DOM IDs", () => {
    const expected = "my-suffix";
    const propsData = {
      domIdSuffix: expected,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetInput = wrapper.find("#input-widget-field-" + expected);
    expect(targetInput.exists()).toBe(true);
    const targetFeedback = wrapper.find("#input-widget-feedback-" + expected);
    expect(targetFeedback.exists()).toBe(true);
  });

  test("When the the user enters few charters in the input, Then an event 'update' is emitted with entered text", async () => {
    const propsData = {
      titleLabel: "Enter  Alphanumeric  ID",
      placeholder: "place holder",
      initialValue: "",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const uuidBase62 = "2VSckkBYH2An3dqHEyfRRE"; // proper uuidcode sent
    const inputWidget = wrapper.find("#input-widget-field-");
    inputWidget.element.value = uuidBase62;
    await inputWidget.trigger("input");
    const emittedEvents = wrapper.emitted("update:value");
    expect(emittedEvents).toHaveLength(1);
    expect(emittedEvents).toStrictEqual([["2VSckkBYH2An3dqHEyfRRE"]]);
  });
  test("When the component is mounted with some invalid text present as a prop, Then the error text is rendered in the DOM", async () => {
    const expectedText = "This field is required";
    const propsData = {
      invalidText: expectedText,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetDiv = wrapper.find(".div__input-controls-content-feedback");
    expect(targetDiv.text()).toStrictEqual(expectedText);
  });
  test("When the Component is mounted with the spellcheck prop set to false, Then the input field in the DOM has the spellcheck attribute set to false", async () => {
    const propsData = {
      spellcheck: false,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const inputWidget = wrapper.find("#input-widget-field-");
    expect(inputWidget.html()).toContain('spellcheck="false"');
  });
  test("Given the component is mounted with the disabled prop set to True, When the user enters few charters in the input, Then no update:value event should be emitted because the field is disabled", async () => {
    const propsData = {
      disabled: true,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const inputWidget = wrapper.find("#input-widget-field-");
    expect(inputWidget.html()).toContain("disabled");

    const userdata = "bdukeusaued"; // proper uuidcode sent
    inputWidget.element.value = userdata;
    await inputWidget.trigger("input");
    const parentIdEvents = wrapper.emitted("update:value");
    expect(parentIdEvents).toBeUndefined();
  });
  test("When the component is mounted, Then the widget width is modified in proption to that of the value set from the props value 'entryWidth'", async () => {
    const propsData = {
      titleLabel: "Enter  Alphanumeric  ID",
      inputWidth: 390,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const background = wrapper.find(".div__input-background");
    expect(background.attributes("style")).toStrictEqual("width: 394px; height: 100px;");
    const inputTitleLabel = wrapper.find(".span__input-content-label");
    expect(inputTitleLabel.attributes("style")).toStrictEqual("width: 390px;");
    const inputBoundedDiv = wrapper.find(".div__input-controls-content-widget");
    expect(inputBoundedDiv.attributes("style")).toStrictEqual("width: 390px; height: 45px; top: 40px;");
    const inputTextEntrySpan = wrapper.find(".span__input-controls-content-input-txt-widget");
    expect(inputTextEntrySpan.attributes("style")).toStrictEqual(
      "width: 390px; height: 45px; line-height: 45px;"
    );
    const inputTextEntryFeedback = wrapper.find(".div__input-controls-content-feedback");
    expect(inputTextEntryFeedback.attributes("style")).toStrictEqual("width: 390px; top: 89px;");
  });
  test("When the component is mounted, Then the widget width is modified in proption to that of the value set from the props value 'entryWidth' in the event of title being empty the height is modified without a hole", async () => {
    const propsData = {
      titleLabel: "",
      placeholder: "place holder",
      initialValue: "",
      invalidText: "This field is required",
      spellcheck: false,
      disabled: false,
      inputWidth: 390,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const background = wrapper.find(".div__input-background");
    expect(background.attributes("style")).toStrictEqual("width: 394px; height: 55px;");
    const inputTitleLabel = wrapper.find(".span__input-content-label");
    expect(inputTitleLabel.exists()).toBe(false);

    const inputBoundedDiv = wrapper.find(".div__input-controls-content-widget");
    expect(inputBoundedDiv.attributes("style")).toStrictEqual("width: 390px; height: 45px; top: 0px;");
    const inputTextEntrySpan = wrapper.find(".span__input-controls-content-input-txt-widget");
    expect(inputTextEntrySpan.attributes("style")).toStrictEqual(
      "width: 390px; height: 45px; line-height: 45px;"
    );
    const inputTextEntryFeedback = wrapper.find(".div__input-controls-content-feedback");
    expect(inputTextEntryFeedback.attributes("style")).toStrictEqual("width: 390px; top: 49px;");
  });
  test("When the component is mounted with the displayTextMessage prop set to false, Then the invalidText is not rendered", async () => {
    const propsData = {
      titleLabel: "",
      placeholder: "place holder",
      initialValue: "",
      invalidText: "This field is required",
      spellcheck: false,
      disabled: false,
      inputWidth: 390,
      displayTextMessage: false,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const inputTextEntryFeedback = wrapper.find(".div__input-controls-content-feedback");
    expect(inputTextEntryFeedback.isVisible()).toBe(false);
  });
  test("Given the component was mounted with the displayTextMessage prop set to false, When the displayTextMessage prop is updated to True, Then the invalidText is rendered", async () => {
    const propsData = {
      titleLabel: "",
      placeholder: "place holder",
      initialValue: "",
      invalidText: "This field is required",
      spellcheck: false,
      disabled: false,
      inputWidth: 390,
      displayTextMessage: false,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const inputTextEntryFeedback = wrapper.find(".div__input-controls-content-feedback");
    expect(inputTextEntryFeedback.isVisible()).toBe(false);
    await wrapper.setProps({ displayTextMessage: true });
    expect(inputTextEntryFeedback.isVisible()).toBe(true);
  });
  test("When an the props cutPasteDisable is set to true, Then validate its not updated on input and onpaste attribute has script with 'return false;'", async () => {
    const propsData = {
      titleLabel: "",
      placeholder: "place holder",
      initialValue: "",
      invalidText: "This field is required",
      spellcheck: false,
      disabled: false,
      inputWidth: 390,
      displayTextMessage: false,
      disablePaste: true,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const mEvent = {
      clipboardData: { getData: jest.fn().mockReturnValueOnce("12") },
    };
    wrapper.find("#input-widget-field-").trigger("paste", mEvent);
    await wrapper.vm.$nextTick(); // wait for update
    expect(wrapper.find("#input-widget-field-").value).toBeUndefined();
    expect(wrapper.find("#input-widget-field-").html()).toContain('onpaste="true"');
  });
  test("When an the props change to render validate class, Then the corresponding validation class should be returned", async () => {
    const propsData = {
      titleLabel: "",
      placeholder: "place holder",
      initialValue: "",
      invalidText: "",
      spellcheck: false,
      disabled: false,
      inputWidth: 390,
      displayTextMessage: false,
      disablePaste: true,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    await wrapper.setProps({ initialValue: "test" });

    expect(wrapper.vm.inputIsValid).toBe(true);
    expect(wrapper.find(".div__input-controls-content-widget--valid")).toBeTruthy();
  });
  test("When an the props change to render invalid class, Then the corresponding validation class should be returned", async () => {
    const propsData = {
      titleLabel: "",
      placeholder: "place holder",
      initialValue: "",
      invalidText: "invalid text",
      spellcheck: false,
      disabled: false,
      inputWidth: 390,
      displayTextMessage: false,
      disablePaste: true,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });

    expect(wrapper.vm.inputIsValid).toBe(false);
    expect(wrapper.find(".div__input-controls-content-widget--invalid")).toBeTruthy();
  });
});
