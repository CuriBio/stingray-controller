import { mount } from "@vue/test-utils";
import SimulationMode from "@/components/status/SimulationMode.vue";
import { SimulationMode as dist_SimulationMode } from "@/dist/stingray.common";
import { shallowMount } from "@vue/test-utils";
import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("SimulationMode.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => wrapper.destroy());
  test("initially the simulationMode is set to false ", async () => {
    const propsData = {};
    wrapper = shallowMount(SimulationMode, { propsData, store, localVue });

    const targetButton = wrapper.find(".div__simulationmode");

    expect(targetButton.isVisible()).toBe(false);
  });
  test("Vuex mutation of simulationMode is set to true component becomes visible ", async () => {
    const propsData = {};
    wrapper = shallowMount(SimulationMode, { propsData, store, localVue });

    store.commit("system/setSimulationStatus", true);
    await wrapper.vm.$nextTick(); // wait for update
    const targetButton = wrapper.find(".div__simulationmode");

    expect(targetButton.isVisible()).toBe(true);
  });
  test("Vuex mutation of simulationMode is set to false component becomes hidden ", async () => {
    const propsData = {};
    wrapper = shallowMount(SimulationMode, { propsData, store, localVue });

    store.commit("system/setSimulationStatus", false);
    await wrapper.vm.$nextTick(); // wait for update
    const targetButton = wrapper.find(".div__simulationmode");

    expect(targetButton.isVisible()).toBe(false);
  });
});
