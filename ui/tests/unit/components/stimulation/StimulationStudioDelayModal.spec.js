import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioInputModal from "@/components/stimulation/StimulationStudioInputModal.vue";
import { MIN_SUBPROTOCOL_DURATION_MS, MAX_SUBPROTOCOL_DURATION_MS } from "@/store/modules/stimulation/enums";
import Vuex from "vuex";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("StimulationStudioInputModal.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  test("When a user closes delay modal, Then button label and new delay value should be emitted to parent component", async () => {
    const wrapper = mount(StimulationStudioInputModal, {
      store,
      localVue,
      propsData: {
        currentColor: "hsla(50, 100%, 50%, 1)",
      },
    });

    await wrapper.find("#input-widget-field-delay").setValue(MIN_SUBPROTOCOL_DURATION_MS.toString());
    await wrapper.findAll(".span__button-label").at(1).trigger("click");

    expect(wrapper.emitted("delayClose")).toBeTruthy();
  });

  test.each([
    [true, ["Save", "Duplicate", "Delete", "Cancel"]],
    [false, ["Save", "Cancel"]],
  ])(
    "When a user opens the delay modal and editing is %s, Then button labels should be %s",
    async (modalOpenForEdit, expectedButtonLabels) => {
      const buttonLabels = StimulationStudioInputModal.computed.buttonLabels.call({
        modalOpenForEdit,
      });
      expect(buttonLabels).toStrictEqual(expectedButtonLabels);
    }
  );

  test.each([
    [true, ["#19ac8a", "#19ac8a", "#bd4932", "#bd4932"]],
    [false, ["#19ac8a", "#bd4932"]],
  ])(
    "When a user opens the delay modal and editing is %s, Then button hover colors should be %s",
    async (modalOpenForEdit, expectedButtonColors) => {
      const buttonLabels = StimulationStudioInputModal.computed.buttonHoverColors.call({
        modalOpenForEdit,
      });
      expect(buttonLabels).toStrictEqual(expectedButtonColors);
    }
  );

  test("When a user adds a value to an input field, Then the correct error message will be presented upon validity checks to input", async () => {
    const wrapper = mount(StimulationStudioInputModal, {
      store,
      localVue,
      propsData: {
        currentColor: "hsla(50, 100%, 50%, 1)",
      },
    });
    const targetInputField = wrapper.find("#input-widget-field-delay");

    // invalid
    await targetInputField.setValue("");
    expect(wrapper.vm.invalidText).toBe("Required");

    await targetInputField.setValue("test");
    expect(wrapper.vm.invalidText).toBe("Must be a (+) number");

    await targetInputField.setValue(`${MIN_SUBPROTOCOL_DURATION_MS - 1}`);
    expect(wrapper.vm.invalidText).toBe(`Duration must be >=${MIN_SUBPROTOCOL_DURATION_MS}ms`);

    await targetInputField.setValue(`${MAX_SUBPROTOCOL_DURATION_MS + 1}`);
    expect(wrapper.vm.invalidText).toBe("Duration must be <= 24hrs");

    await targetInputField.setValue(`${MIN_SUBPROTOCOL_DURATION_MS + 0.1}`);
    expect(wrapper.vm.invalidText).toBe("Must be a whole number of ms");

    // valid
    await targetInputField.setValue(`${MIN_SUBPROTOCOL_DURATION_MS}`);
    expect(wrapper.vm.invalidText).toBe("");

    await targetInputField.setValue(`${MAX_SUBPROTOCOL_DURATION_MS}`);
    expect(wrapper.vm.invalidText).toBe("");
  });

  test("When a user wants to save the delay/repeat value, Then it will only be possible once a all validation checks pass for input", async () => {
    const wrapper = mount(StimulationStudioInputModal, {
      store,
      localVue,
      propsData: {
        modalType: "Delay",
        currentColor: "hsla(50, 100%, 50%, 1)",
      },
    });
    await wrapper.find("#input-widget-field-delay").setValue("5000");
    expect(wrapper.vm.isValid).toBe(true);

    await wrapper.find("#input-widget-field-delay").setValue("test");
    expect(wrapper.vm.isValid).toBe(false);
  });
  test("When a user selects a different time unit from the dropdown, Then the index will be saved to state", async () => {
    const wrapper = mount(StimulationStudioInputModal, {
      store,
      localVue,
      propsData: {
        currentColor: "hsla(50, 100%, 50%, 1)",
      },
    });

    await wrapper.find(".div__small-dropdown-controls-content-widget").trigger("click");
    await wrapper.findAll("li").at(0).trigger("click");

    expect(wrapper.vm.timeUnitIdx).toBe(1);
  });

  test("When a user clicks on a new color for delay block, Then the color will be set to state to be emitted to parent component", async () => {
    const wrapper = mount(StimulationStudioInputModal, {
      store,
      localVue,
      propsData: {
        currentColor: "hsla(50, 100%, 50%, 1)",
      },
    });

    await wrapper.find(".div__color-label").trigger("click");

    await wrapper.findAll(".individual-color-block").at(0).trigger("click");

    expect(wrapper.vm.selectedColor).toBe("hsla(0, 100%, 50%, 1)");
  });
});
