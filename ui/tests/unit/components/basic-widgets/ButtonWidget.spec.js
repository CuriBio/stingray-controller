import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/basic-widgets/ButtonWidget.vue";
import { ButtonWidget as DistComponentToTest } from "@/dist/mantarray.common";
import { shallowMount } from "@vue/test-utils";

import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);

let NuxtStore;
let store;

describe("ButtonWidget.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  test("When mounting ButtonWidget from the build dist file, Then it loads successfully and the black box is displayed", () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = shallowMount(DistComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetBackgroundDiv = wrapper.find(".div__button-background");
    expect(targetBackgroundDiv.isVisible()).toBe(true);
  });
  test("When that ButtonWidget is mounted, Then the button width/height/top and left gets applied based on the values from the props", () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
      buttonBackgroundColor: "rgb(255, 255, 255)",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetBackgroundDiv = wrapper.find(".div__button-background");
    expect(targetBackgroundDiv.attributes().style).toBe(
      "width: 500px; height: 50px; top: 0px; left: 0px; background: rgb(255, 255, 255);"
    );
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, button label, visible, focus color and greyed color the values provided from the props as visible is true so focus color text is rendred", () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.find(".span__button-label");
    expect(targetButtonLabelBtn.text()).toStrictEqual("Save ID");
    expect(targetButtonLabelBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 500px; left: 0px; cursor: pointer;"
    ); // DOM converts the #FFFFFF to rgb(255, 255, 255)
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, button label, visible, focus color and greyed color the values provided from the props as visible is false a greyed color text is rendred", () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [false],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.find(".span__button-label");
    expect(targetButtonLabelBtn.text()).toStrictEqual("Save ID");
    expect(targetButtonLabelBtn.attributes().style).toBe("color: rgb(63, 63, 63); width: 500px; left: 0px;"); // DOM converts the #3F3F3F to rgb(63, 63, 63)
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, button label, visible, focus color and greyed color the values provided from the props as visible is false a greyed color text, on a prop update of visible to true the enabled color text is rendered", async () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [false],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.find(".span__button-label");
    expect(targetButtonLabelBtn.text()).toStrictEqual("Save ID");
    expect(targetButtonLabelBtn.attributes().style).toBe("color: rgb(63, 63, 63); width: 500px; left: 0px;"); // DOM converts the #3F3F3F to rgb(63, 63, 63)

    const updatedPropsData = {
      isEnabled: [true],
    };

    await wrapper.setProps(updatedPropsData);
    expect(targetButtonLabelBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 500px; left: 0px; cursor: pointer;"
    ); // DOM converts the #FFFFFF to rgb(255, 255, 255)
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, button label, visible, focus color, greyed color, hover color the values provided from the props as visible is true so focus color text is rendred, user hover the hover color is rendered", async () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.find(".span__button-label");
    await targetButtonLabelBtn.trigger("mouseenter");
    expect(targetButtonLabelBtn.attributes().style).toBe(
      "color: rgb(189, 73, 50); width: 500px; left: 0px; cursor: pointer;"
    );
    await targetButtonLabelBtn.trigger("mouseleave");
    expect(targetButtonLabelBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 500px; left: 0px; cursor: pointer;"
    );
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, button label, hover color, without enabledColor prop from the props as visible is true so focus color text is rendred", async () => {
    const propsData = {
      buttonNames: ["Save ID"],
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.find(".span__button-label");
    expect(targetButtonLabelBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 500px; left: 0px; cursor: pointer;"
    );
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, button label, hover color, without disabledColor prop from the props as visible is false so greyed color text is rendred", async () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      isEnabled: [false],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.find(".span__button-label");
    expect(targetButtonLabelBtn.attributes().style).toBe("color: rgb(63, 63, 63); width: 500px; left: 0px;");
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, with buttons label Cancel/Delete ID/Save ID is placed with equal width of 1/3 that of widget and shifted from left at rate of 0, 1/3 and 2/3", async () => {
    const propsData = {
      buttonNames: ["Cancel", "Delete ID", "Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true, true, false],
      hoverColor: ["#BD4932", "#BD4932", "#19ac8a"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
    const cancelBtn = targetButtonLabelBtn.at(0);
    expect(cancelBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 166.66666666666666px; left: 0px; cursor: pointer;"
    );
    const deleteBtn = targetButtonLabelBtn.at(1);
    expect(deleteBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 166.66666666666666px; left: 166.66666666666666px; cursor: pointer;"
    );
    const saveBtn = targetButtonLabelBtn.at(2);
    expect(saveBtn.attributes().style).toBe(
      "color: rgb(63, 63, 63); width: 166.66666666666666px; left: 333.3333333333333px;"
    );
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, with buttons label Cancel/Delete ID/Save ID as default all buttons are enabled and have enabledColor for color", async () => {
    const propsData = {
      buttonNames: ["Cancel", "Delete ID", "Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      hoverColor: ["#BD4932", "#BD4932", "#19ac8a"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
    const cancelBtn = targetButtonLabelBtn.at(0);
    expect(cancelBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 166.66666666666666px; left: 0px; cursor: pointer;"
    );
    const deleteBtn = targetButtonLabelBtn.at(1);
    expect(deleteBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 166.66666666666666px; left: 166.66666666666666px; cursor: pointer;"
    );
    const saveBtn = targetButtonLabelBtn.at(2);
    expect(saveBtn.attributes().style).toBe(
      "color: rgb(255, 255, 255); width: 166.66666666666666px; left: 333.3333333333333px; cursor: pointer;"
    );
  });
  test("When the ButtonWidget is mounted, Then it loads the horizontal top-line divider proportion, to the defined width of 490px with padding from edges of the widget length", async () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetCanvasCommonLine = wrapper.find(".canvas__common-horizontal-line");
    expect(targetCanvasCommonLine.attributes().style).toBe("width: 490px;"); // validated if dynamically the value is modified to n-10 px in width as 5px padding is as per mockflow
  });
  test("When the ButtonWidget is mounted, Then it loads the widget as there is only one single btn label Save ID, verify that vertical line is not present", async () => {
    const propsData = {
      buttonNames: ["Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true],
      hoverColor: ["#BD4932"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetCanvasVerticalLine = wrapper.find(".canvas__vertical-line");
    expect(targetCanvasVerticalLine.exists()).toBe(false);
  });
  test("When that ButtonWidget is mounted, Then it loads the button background, with buttons label Cancel/Delete ID/Save ID in between them a vertical line between button labels is rendered", async () => {
    const propsData = {
      buttonNames: ["Cancel", "Delete ID", "Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true, true, false],
      hoverColor: ["#BD4932", "#BD4932", "#19ac8a"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetVerticalLine = wrapper.findAll(".canvas__vertical-line");

    const firstVerticalLine = targetVerticalLine.at(0);
    expect(firstVerticalLine.attributes().style).toBe("left: 166.66666666666666px;");
    const secondVerticalLine = targetVerticalLine.at(1);
    expect(secondVerticalLine.attributes().style).toBe("left: 333.3333333333333px;");
  });
  test("Given the ButtonWidget is mounted with Cancel / Save ID buttons and Save is disabled, When User clicks on Cancel, Then an event is emmitted with the Button Index as the contents of the event", async () => {
    const propsData = {
      buttonNames: ["Cancel", "Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true, false],
      hoverColor: ["#BD4932", "#19ac8a"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
    const cancelBtn = targetButtonLabelBtn.at(0);
    await cancelBtn.trigger("click");
    const parentIdEvents = wrapper.emitted("btn-click");
    expect(parentIdEvents).toHaveLength(1);
    expect(parentIdEvents).toStrictEqual([[0]]);
  });
  test("Given the ButtonWidget is mounted with Cancel / Save ID buttons and Save is disabled, When User clicks on Save, Then no event is emmitted when disabled button of Save is clicked", async () => {
    const propsData = {
      buttonNames: ["Cancel", "Save ID"],
      enabledColor: "#FFFFFF",
      disabledColor: "#3F3F3F",
      isEnabled: [true, false],
      hoverColor: ["#BD4932", "#19ac8a"],
      buttonWidgetWidth: 500,
      buttonWidgetHeight: 50,
      buttonWidgetTop: 0,
      buttonWidgetLeft: 0,
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetButtonLabelBtn = wrapper.findAll(".span__button-label");
    const saveBtn = targetButtonLabelBtn.at(1);
    await saveBtn.trigger("click");
    const parentIdEvents = wrapper.emitted("btn-click");
    expect(parentIdEvents).toBeUndefined();
    expect(parentIdEvents).toBeUndefined();
  });
});
