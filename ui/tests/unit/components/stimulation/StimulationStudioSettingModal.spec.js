import { mount, shallowMount, createLocalVue } from "@vue/test-utils";
import StimulationStudioWaveformSettingModal from "@/components/stimulation/StimulationStudioWaveformSettingModal.vue";
import { StimulationStudioWaveformSettingModal as dist_StimulationStudioWaveformSettingModal } from "@/dist/stingray.common";
import { MIN_SUBPROTOCOL_DURATION_MS } from "@/store/modules/stimulation/enums";
import Vuex from "vuex";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

const testBiphasicPulseSettings = {
  phaseOneDuration: "",
  phaseOneCharge: "",
  interphaseInterval: "",
  phaseTwoDuration: "",
  phaseTwoCharge: "",
  postphaseInterval: "",
  totalActiveDuration: {
    duration: "",
    unit: "milliseconds",
  },
  numCycles: 0,
  frequency: "",
};

const testMonophasicPulseSettings = {
  phaseOneDuration: "",
  phaseOneCharge: "",
  postphaseInterval: "",
  totalActiveDuration: {
    duration: "",
    unit: "milliseconds",
  },
  numCycles: 0,
  frequency: "",
};

describe("StimulationStudioWaveformSettingModal.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  test("When mounting StimulationStudioWaveformSettingModal from the build dist file, Then the title text `Biphasic Pulse Details` loads correctly and initial error messages for each input", () => {
    const expectedErrMsgs = {
      phaseOneDuration: "Required",
      phaseOneCharge: "Required",
      interphaseInterval: "Required",
      phaseTwoDuration: "Required",
      phaseTwoCharge: "Required",
      pulseFrequency: "Required",
      totalActiveDuration: "Required",
      numCycles: "Must be a whole number > 0",
    };
    wrapper = mount(dist_StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        selectedPulseSettings: testBiphasicPulseSettings,
        frequency: 0,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });

    const targetSpan = wrapper.find(".span__stimulationstudio-current-settings-title");
    expect(wrapper.vm.errMsgs).toStrictEqual(expectedErrMsgs);

    expect(targetSpan).toBeTruthy();
  });
  test("When mounting StimulationStudioWaveformSettingModal from the component file, Then it loads successfully  `Biphasic Pulse Details` as defined title text is rendered", () => {
    wrapper = shallowMount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        selectedPulseSettings: testBiphasicPulseSettings,
        frequency: 0,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });
    const targetSpan = wrapper.find(".span__stimulationstudio-current-settings-title");
    expect(targetSpan).toBeTruthy();
  });
  test("When clicking on either button, Then the modal successfully closes by emitting the close() function to parent component", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        selectedPulseSettings: testBiphasicPulseSettings,
        frequency: 0,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });
    await wrapper.vm.close(0);
    expect(wrapper.emitted("close", "Save")).toBeTruthy();
  });
  test("When Voltage and Biphasic props is passed down, Then the correct labels should be present in modal and not default", async () => {
    const wrapper = shallowMount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Biphasic",
        selectedPulseSettings: testBiphasicPulseSettings,
        frequency: 0,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });
    const title = wrapper.findAll("span").at(6).text();
    expect(title).toBe("Voltage");
    const interphaseLabel = wrapper.findAll("span").at(8);
    expect(interphaseLabel).toBeTruthy();
  });

  test("When a user opens the pulse settings modal, Then the user can only save the settings if all inputs pass the validity checks", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Current",
        pulseType: "Monophasic",
        selectedPulseSettings: testMonophasicPulseSettings,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });

    const expectedEnabledArray = [true, true];
    const expectedSettings = {
      phaseOneDuration: 10,
      phaseOneCharge: 50,
    };
    await wrapper.find("#input-widget-field-duration").setValue("10");
    await wrapper.find("#input-widget-field-charge").setValue("50");
    await wrapper.find("#input-widget-field-pulse-frequency").setValue("20");
    await wrapper
      .find("#input-widget-field-total-active-duration")
      .setValue(MIN_SUBPROTOCOL_DURATION_MS.toString());

    expect(wrapper.vm.allValid).toBe(true);
    expect(wrapper.vm.isEnabledArray).toStrictEqual(expectedEnabledArray);
    expect(wrapper.vm.activeDurationIdx).toBe(0);
    expect(wrapper.vm.pulseSettings.phaseOneDuration).toBe(expectedSettings.phaseOneDuration);
    expect(wrapper.vm.pulseSettings.phaseOneCharge).toBe(expectedSettings.phaseOneCharge);

    await wrapper.find("#input-widget-field-charge").setValue("-101");
    expect(wrapper.vm.allValid).toBe(false);
  });

  test("When a user adds a value to an input field, Then the correct error message will be presented upon validity checks to input", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Monophasic",
        selectedPulseSettings: testMonophasicPulseSettings,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });
    const targetInputField = wrapper.find("#input-widget-field-duration");

    await targetInputField.setValue("test");
    expect(wrapper.vm.errMsgs.phaseOneDuration).toBe("Must be a positive number");

    await targetInputField.setValue("1500");
    expect(wrapper.vm.errMsgs.phaseOneDuration).toBe("Duration must be <= 50ms");

    await targetInputField.setValue("");
    expect(wrapper.vm.errMsgs.phaseOneDuration).toBe("Required");
  });

  test("Given that a high frequency is selected, When a user adds a value to an input field, Then the correct error message will be presented upon validity checks to input", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Monophasic",
        selectedPulseSettings: testMonophasicPulseSettings,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });

    await wrapper.setData({ inputPulseFrequency: 100 });

    const targetInputField = wrapper.find("#input-widget-field-duration");
    await targetInputField.setValue("11");
    expect(wrapper.vm.errMsgs.phaseOneDuration).toBe("Duration must be <= 8ms");
  });

  test("When a user adds a value to the total active duration, Then the value must be a number greater than the min allowed subprotocol duration", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Biphasic",
        selectedPulseSettings: {
          phaseOneDuration: 10,
          phaseOneCharge: 100,
          interphaseInterval: 10,
          phaseTwoDuration: 10,
          phaseTwoCharge: -100,
          postphaseInterval: 20,
          totalActiveDuration: {
            duration: 30,
            unit: "milliseconds",
          },
          numCycles: 10,
          frequency: 5,
        },
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });
    const targetInputField = wrapper.find("#input-widget-field-total-active-duration");

    await targetInputField.setValue((MIN_SUBPROTOCOL_DURATION_MS - 1).toString());
    expect(wrapper.vm.errMsgs.totalActiveDuration).toBe(`Must be >= ${MIN_SUBPROTOCOL_DURATION_MS}ms`);

    await targetInputField.setValue((-(MIN_SUBPROTOCOL_DURATION_MS - 1)).toString());
    expect(wrapper.vm.errMsgs.totalActiveDuration).toBe(`Must be >= ${MIN_SUBPROTOCOL_DURATION_MS}ms`);

    await targetInputField.setValue(MIN_SUBPROTOCOL_DURATION_MS.toString());
    expect(wrapper.vm.errMsgs.totalActiveDuration).toBe("");

    await targetInputField.setValue("");
    expect(wrapper.vm.errMsgs.totalActiveDuration).toBe("Required");
  });

  test("When a user changes a the unit of time in the setting modal, Then the change will trigger a new validation check and record new selected index", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Biphasic",
        selectedPulseSettings: {
          phaseOneDuration: 5,
          phaseOneCharge: 30,
          interphaseInterval: 5,
          phaseTwoDuration: 5,
          phaseTwoCharge: -10,
          postphaseInterval: 485,
          totalActiveDuration: {
            duration: 1,
            unit: "seconds",
          },
          numCycles: 2,
          frequency: 2,
        },
        currentColor: "hsla(100, 100%, 50%, 1)",
        modalOpenForEdit: true,
      },
    });

    expect(wrapper.vm.allValid).toBe(true);

    wrapper.findAll(".div__small-dropdown-controls-content-widget").at(0).trigger("click");

    await wrapper.findAll("li").at(0).trigger("click");

    expect(wrapper.vm.allValid).toBe(false);
    expect(wrapper.vm.activeDurationIdx).toBe(0);
  });

  test("When a user closes the modal on Save, Then correct repeat delay interval will get calculated from the pulse frequency", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Monophasic",
        selectedPulseSettings: testMonophasicPulseSettings,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });
    wrapper.setData({
      pulseSettings: {
        phaseOneDuration: "5",
        phaseOneCharge: "300",
        interphaseInterval: "0",
        phaseTwoDuration: "0",
        phaseTwoCharge: "0",
        postphaseInterval: "",
        totalActiveDuration: {
          duration: "1",
          unit: "seconds",
        },
        numCycles: 10,
        frequency: 10,
      },
      inputPulseFrequency: 10,
      activeDurationIdx: 2,
      allValid: true,
    });
    await wrapper.vm.close(0);
    expect(wrapper.vm.pulseSettings.postphaseInterval).toBe(95);
  });

  test.each([
    [true, ["Save", "Duplicate", "Delete", "Cancel"]],
    [false, ["Save", "Cancel"]],
  ])(
    "When a user opens the delay modal and editing is %s, Then button labels should be %s",
    async (modalOpenForEdit, expectedButtonLabels) => {
      const buttonLabels = StimulationStudioWaveformSettingModal.computed.buttonLabels.call({
        modalType: "Monophasic",
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
      const buttonLabels = StimulationStudioWaveformSettingModal.computed.buttonHoverColors.call({
        modalType: "Monophasic",
        modalOpenForEdit,
      });
      expect(buttonLabels).toStrictEqual(expectedButtonColors);
    }
  );

  test("When a user clicks on a new color for a waveform pulse, Then the color will be set to state to be emitted to parent component", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Monophasic",
        selectedPulseSettings: testMonophasicPulseSettings,
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });

    await wrapper.find(".div__color-label").trigger("click");

    await wrapper.findAll(".individual-color-block").at(0).trigger("click");

    expect(wrapper.vm.selectedColor).toBe("hsla(0, 100%, 50%, 1)");
  });

  test("When selects to use number of cycles instead of total active duration, Then total active duration will get updated as user changes number of cycles", async () => {
    const wrapper = mount(StimulationStudioWaveformSettingModal, {
      store,
      localVue,
      propsData: {
        stimulationType: "Voltage",
        pulseType: "Biphasic",
        selectedPulseSettings: {
          phaseOneDuration: 5,
          phaseOneCharge: 30,
          interphaseInterval: 5,
          phaseTwoDuration: 5,
          phaseTwoCharge: -10,
          postphaseInterval: 485,
          totalActiveDuration: {
            duration: 1,
            unit: "seconds",
          },
          numCycles: 2,
          frequency: 2,
        },
        currentColor: "hsla(100, 100%, 50%, 1)",
        modalOpenForEdit: true,
      },
    });

    expect(wrapper.vm.allValid).toBe(true);
    expect(wrapper.vm.calculatedActiveDur).toBe(1);

    const targetCheckboxBtn = wrapper.findAll('input[type="checkbox"]');
    await targetCheckboxBtn.at(0).setChecked(true);

    await wrapper.find("#input-widget-field-num-cycles").setValue("5");
    expect(wrapper.vm.calculatedActiveDur).toBe(2.5);
  });
});
