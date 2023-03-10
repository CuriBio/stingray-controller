import { mount } from "@vue/test-utils";
import BootstrapVue from "bootstrap-vue";
import StatusWidget from "@/components/status/StatusBar.vue";
import Vue from "vue";
import Vuex from "vuex";
import axios from "axios";
const MockAxiosAdapter = require("axios-mock-adapter");
import { createLocalVue } from "@vue/test-utils";
import { STATUS } from "@/store/modules/system/enums";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(BootstrapVue);

let NuxtStore;
let store;
let mockedAxios;

const textSelector = ".span__status-bar-text";

describe("StatusWidget.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    mockedAxios = new MockAxiosAdapter(axios);
  });

  afterEach(() => {
    wrapper.destroy();
    mockedAxios.restore();
  });
  describe("systemStatus", () => {
    // add test to check that false = not visible
    test.each([
      ["SERVER_INITIALIZING_STATE", "Status: Booting Up..."],
      ["SERVER_READY_STATE", "Status: Connecting..."],
      ["INSTRUMENT_INITIALIZING_STATE", "Status: Initializing..."],
      ["CHECKING_FOR_UPDATES_STATE", "Status: Checking for Firmware Updates..."],
      ["UPDATES_NEEDED_STATE", "Status: Firmware Updates Required"],
      ["DOWNLOADING_UPDATES_STATE", "Status: Downloading Firmware Updates..."],
      ["INSTALLING_UPDATES_STATE", "Status: Installing Firmware Updates..."],
      ["UPDATES_COMPLETE_STATE", "Status: Firmware Updates Complete"],
      ["ERROR_STATE", "Status: Error Occurred"],
      ["UPDATE_ERROR_STATE", "Status: Error During Firmware Update"],
    ])(
      "Given that /shutdown is mocked to return status 200, When Vuex is mutated to the state %s, Then the status text should update to be: %s",
      async (vuexState, expectedText) => {
        const shutdownUrl = "http://localhost:4567/shutdown";
        mockedAxios.onGet(shutdownUrl).reply(200, {});
        const propsData = {};
        wrapper = mount(StatusWidget, {
          propsData,
          store,
          localVue,
        });
        store.commit("system/setStatusUuid", STATUS[vuexState]);
        await wrapper.vm.$nextTick(); // wait for update

        expect(wrapper.find(textSelector).text()).toBe(expectedText);
      }
    );
    test("When initially mounted, Then the status text matches the Vuex state", async () => {
      const propsData = {};
      store.commit("system/setStatusUuid", STATUS.SERVER_READY_STATE);
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("Status: Connecting...");
    });

    test.each([
      "InstrumentCreateConnectionError",
      "InstrumentConnectionLostError",
      "InstrumentBadDataError",
      "InstrumentFirmwareError",
    ])(
      "When unique shutdown error gets set to %s in Vuex, Then it will override any status text present before error modal appears",
      async (errorType) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        expect(wrapper.find(textSelector).text()).toBe("Status: Booting Up..."); // initial status
        await store.commit("system/setShutdownErrorStatus", { errorType });
        expect(wrapper.find(textSelector).text()).toBe(`Status: Error Occurred`);
      }
    );

    test("When unknown error type gets sent through WS, Then the status will still be set to error occurred", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });

      expect(wrapper.find(textSelector).text()).toBe("Status: Booting Up..."); // initial status
      await store.commit("system/setShutdownErrorStatus", { errorType: "UnknownError" });
      expect(wrapper.find(textSelector).text()).toBe("Status: Error Occurred");
    });

    test("When Vuex is mutated to an unknown UUID, Then the status text should update to include that UUID", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });

      store.commit("system/setStatusUuid", "3dbb8814-09f1-44db-b7d5-7a9f702beac4");
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("Status: 3dbb8814-09f1-44db-b7d5-7a9f702beac4");
    });
    test("Given that the http response is 404 for api request /shutdown, When Vuex is mutated to an ERROR_STATE UUID, Then the status text should update as 'Error Occurred' and the the dialog of ErrorCatchWidget is visible", async () => {
      const shutdownUrl = "http://localhost:4567/shutdown";
      mockedAxios.onGet(shutdownUrl).reply(404);
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
        attachToDocument: true,
      });

      expect(wrapper.contains("#error-catch")).toBe(true);
      const modal = wrapper.find("#error-catch");
      expect(modal.isVisible()).toBe(false);
      store.commit("system/setStatusUuid", STATUS.ERROR_STATE);
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("Status: Error Occurred");
      Vue.nextTick(() => {
        expect(modal.isVisible()).toBe(true);
      });
    });
    test("When Vuex is mutated to an ERROR_STATE UUID and shutdown status was set to known error, Then the status text should not update to 'Error Occurred'", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
        attachToDocument: true,
      });

      await store.commit("system/setShutdownErrorStatus", {
        errorType: "InstrumentCreateConnectionError",
      });
      store.commit("system/setStatusUuid", STATUS.ERROR_STATE);
      expect(wrapper.find(textSelector).text()).toBe(`Status: Error Occurred`);
    });
    test("When Vuex is mutated to an UPDATE ERROR UUID, Then the status text should update as 'Error During Firmware Update' and the the dialog of ErrorCatchWidget is visible", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
        attachToDocument: true,
      });

      expect(wrapper.contains("#error-catch")).toBe(true);
      const modal = wrapper.find("#error-catch");

      store.commit("system/setStatusUuid", STATUS.UPDATE_ERROR_STATE);
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("Status: Error During Firmware Update");
      Vue.nextTick(() => {
        expect(modal.isVisible()).toBe(true);
      });

      wrapper.vm.closeModalsById(["error-catch"]); // the event of ok-clicked got invoked.

      Vue.nextTick(() => {
        expect(modal.isVisible()).toBe(false);
      });
    });
    test.each([
      "SERVER_INITIALIZING_STATE",
      "SERVER_READY_STATE",
      "INITIALIZING_INSTRUMENT_STATE",
      "UPDATES_NEEDED_STATE",
      "UPDATES_COMPLETE_STATE",
      "UPDATE_ERROR_STATE",
      "ERROR_STATE",
    ])(
      "When a user wants to exit the desktop app, Then the closure warning modals should not appear if there are no active processes or fw update",
      async (vuexState) => {
        const confirmationSpy = jest.spyOn(StatusWidget.methods, "handleConfirmation");
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });

        await store.commit("system/setStatusUuid", STATUS[vuexState]);
        await store.commit("system/setConfirmationRequest", true);
        expect(confirmationSpy).toHaveBeenCalledWith(1);

        Vue.nextTick(() => {
          expect(wrapper.find("#fw-closure-warning").isVisible()).toBe(false);
          expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(false);
        });
      }
    );

    test.each(["BUFFERING", "LIVE_VIEW_ACTIVE", "RECORDING", "CALIBRATING"])(
      "When a user wants to exit the desktop app, Then the closure warning modal should appear if there are active processes",
      async (vuexState) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        await store.commit("system/setStatusUuid", STATUS[vuexState]);

        await store.commit("system/setConfirmationRequest", false);
        Vue.nextTick(() => {
          expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(false);
        });

        await store.commit("system/setConfirmationRequest", true);
        Vue.nextTick(() => {
          expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(true);
        });
      }
    );

    test("When a user wants to exit the desktop app and a stimulation is active, Then the closure warning modal should appear", async () => {
      wrapper = mount(StatusWidget, {
        store,
        localVue,
      });

      await store.commit("stimulation/setStimPlayState", true);
      await store.commit("system/setConfirmationRequest", false);
      Vue.nextTick(() => {
        expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(false);
      });

      await store.commit("system/setConfirmationRequest", true);
      Vue.nextTick(() => {
        expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(true);
      });
    });

    test.each(["DOWNLOADING_UPDATES", "INSTALLING_UPDATES"])(
      "When a user wants to exit the desktop app, Then the fw closure warning modal should appear if a fw update is in progress",
      async (vuexState) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        await store.commit("system/setStatusUuid", STATUS[vuexState]);

        await store.commit("system/setConfirmationRequest", false);
        Vue.nextTick(() => {
          expect(wrapper.find("#fw-closure-warning").isVisible()).toBe(false);
        });

        await store.commit("system/setConfirmationRequest", true);
        Vue.nextTick(() => {
          expect(wrapper.find("#fw-closure-warning").isVisible()).toBe(true);
        });
      }
    );
  });
  describe("stimStatus", () => {
    test.each([
      ["IDLE_READY_STATE", "NO_PROTOCOLS_ASSIGNED", "Status: No protocols have been assigned", {}],
      ["IDLE_READY_STATE", "CONFIG_CHECK_NEEDED", "Status: Configuration Check Needed", { 1: {} }],
      [
        "IDLE_READY_STATE",
        "CONFIG_CHECK_IN_PROGRESS",
        "Status: Configuration Check in Progress...",
        { 1: {} },
      ],
      ["IDLE_READY_STATE", "CONFIG_CHECK_COMPLETE", "Status: Configuration Check Complete", { 1: {} }],
      ["IDLE_READY_STATE", "READY", "Status: Ready", { 1: {} }],
      ["IDLE_READY_STATE", "STIM_ACTIVE", "Status: Stimulating...", { 1: {} }],
      ["IDLE_READY_STATE", "SHORT_CIRCUIT_ERROR", "Status: Short Circuit Error", {}],
      ["IDLE_READY_STATE", "ERROR", "Status: Error Occurred", {}],
      ["ERROR_STATE", "NO_PROTOCOLS_ASSIGNED", "Status: Error Occurred", {}],
      ["SERVER_INITIALIZING_STATE", "CONFIG_CHECK_NEEDED", "Status: Booting Up...", { 1: {} }],
      ["INSTRUMENT_INITIALIZING_STATE", "CONFIG_CHECK_IN_PROGRESS", "Status: Initializing...", { 1: {} }],
      ["SERVER_READY_STATE", "CONFIG_CHECK_COMPLETE", "Status: Connecting...", { 1: {} }],
      ["UPDATES_NEEDED_STATE", "READY", "Status: Firmware Updates Required", { 1: {} }],
      ["INSTALLING_UPDATES_STATE", "STIM_ACTIVE", "Status: Installing Firmware Updates...", { 1: {} }],
      ["UPDATES_COMPLETE_STATE", "SHORT_CIRCUIT_ERROR", "Status: Firmware Updates Complete", {}],
      ["CHECKING_FOR_UPDATES_STATE", "ERROR_STATE", "Status: Checking for Firmware Updates...", {}],
    ])(
      "When system status is %s and stim's stimStatus gets mutated to %s, Then the status text should update to be %s if system Uuid is IDLE_READY_STATE",
      async (systemVuexState, vuexState, expectedText, assignments) => {
        const propsData = {};
        wrapper = mount(StatusWidget, {
          propsData,
          store,
          localVue,
        });
        await store.commit("system/setStatusUuid", STATUS[systemVuexState]);
        store.state.stimulation.protocolAssignments = assignments;

        await store.commit("stimulation/setStimStatus", STIM_STATUS[vuexState]);
        expect(wrapper.find(textSelector).text()).toBe(expectedText);
      }
    );
  });
});
