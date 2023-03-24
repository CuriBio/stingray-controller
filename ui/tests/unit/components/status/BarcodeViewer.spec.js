import { mount } from "@vue/test-utils";
import BarcodeViewer from "@/components/status/BarcodeViewer.vue";
import { BarcodeViewer as dist_BarcodeViewer } from "@/dist/stingray.common";
import { shallowMount } from "@vue/test-utils";
import { createLocalVue } from "@vue/test-utils";
import { TextValidation } from "@/js-utils/textValidation.js";
import Vue from "vue";

const wrapper = null;

const localVue = createLocalVue();
let NuxtStore;
let store;

describe("BarcodeViewer.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    jest.restoreAllMocks();
  });

  test("When mounting BarcodeViewer from the build dist file, Then it loads successfully text is Not Recording and time is null", () => {
    const propsData = {};
    const wrapper = shallowMount(dist_BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    expect(wrapper.find(".span__plate-barcode-text").text()).toBe("Plate Barcode:");
  });

  test("Given a valid barcode has been into the Vuex, When the component is mounted, Then the text of the Barcode Input field should be valid barcode string and Red Box is visible", async () => {
    store.dispatch("system/validateBarcode", { type: "plateBarcode", newValue: "ML2022053000" });
    const propsData = {};
    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    await wrapper.vm.$nextTick(); // wait for update
    expect(wrapper.find("input").element.value).toBe("ML2022053000");
    expect(wrapper.find(".input__plate-barcode-entry-valid").isVisible()).toBe(true);
  });

  test("Given a invalid barcode has been into the Vuex, When the component is mounted, Then the text of the Barcode Input field should be valid barcode string and Green Box is visible", async () => {
    store.dispatch("system/validateBarcode", { type: "plateBarcode", newValue: "MA209990004" });
    const propsData = {};
    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    await wrapper.vm.$nextTick(); // wait for update
    expect(wrapper.find("input").element.value).toBe("MA209990004");
    expect(wrapper.find(".input__plate-barcode-entry-invalid").isVisible()).toBe(true);
  });

  test("Given that barcode entry is in manual mode, When a plate barcode is entered, Then it is stored in Vuex playback store correctly", async () => {
    const spiedTextValidator = jest.spyOn(TextValidation.prototype, "validateBarcode");
    const propsData = {};
    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    store.commit("system/setBarcodeManualMode", true);
    expect(store.state.system.barcodes.plateBarcode.value).toBeNull();
    const testBarcode = "ML2022001000";

    await wrapper.vm.handleManualModeChoice(true);
    await wrapper.find("input").setValue(testBarcode);
    expect(spiedTextValidator).toHaveBeenCalledWith(testBarcode, "plateBarcode");
    expect(store.state.system.barcodes.plateBarcode.value).toBe(testBarcode);
  });

  test("Given that its in manual mode and that the User entered a valid barcode, When user tries to enter barcode with an additional 13th digit, then it is not considered valid in Vuex", async () => {
    const propsData = {};

    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    await wrapper.vm.handleManualModeChoice(true);

    wrapper.find("input").setValue("ML2022053000"); // test case will fail on delating if (barcodeLen >= 10 && barcodeLen < 12) in API validateBarcodeViewer()
    await wrapper.vm.$nextTick(); // wait for update
    // confirm pre-condition
    expect(store.state.system.barcodes.plateBarcode.valid).toBe(true);
    await wrapper.find("input").setValue("ML20220530003");
    expect(store.state.system.barcodes.plateBarcode.valid).toBe(false);
  });
  test("Set a proper plate barcode and validate that no the red squiggle line is not present", async () => {
    const propsData = {};

    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });
    await wrapper.find("input").setValue("M120044099");
    expect(wrapper.find("input").html()).toContain('spellcheck="false"');
  });

  test("Fire an event to paste text ABCD validate its not updated on input", async () => {
    const propsData = {};

    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    await wrapper.vm.handleManualModeChoice(true);

    const mEvent = {
      clipboardData: { getData: jest.fn().mockReturnValueOnce("12") },
    };
    await wrapper.find("input").trigger("paste", mEvent);
    expect(wrapper.find("input").value).toBeUndefined();
  });

  test("When user closes barcode-warning modal, Then barcodeWarning will get reset in state", async () => {
    const propsData = {};

    const wrapper = mount(BarcodeViewer, {
      propsData,
      store,
      localVue,
      attachToDocument: true,
    });

    await store.commit("system/setBarcodeWarning", true);
    expect(store.state.system.barcodeWarning).toBe(true);

    Vue.nextTick(() => {
      expect(wrapper.find("barcode-warning").isVisible()).toBe(true);
    });

    // call function that gets emitted from status modal
    await wrapper.vm.closeWarningModal();

    expect(store.state.system.barcodeWarning).toBe(false);
  });
});
