import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioZoomControls from "@/components/stimulation/StimulationStudioZoomControls.vue";
import Vuex from "vuex";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("StimulationStudioZoomControls.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  test("When a user clicks on the minus icon to zoom out on an axis, Then the specified scale should multiply by 1.5", async () => {
    const wrapper = mount(StimulationStudioZoomControls, {
      localVue,
      store,
      propsData: {
        axis: "y-axis",
      },
    });
    const expectedScale = 180;
    expect(store.state.stimulation.yAxisScale).toBe(120);
    await wrapper.find(".span__axis-controls-zoom-out-button").trigger("click");
    expect(store.state.stimulation.yAxisScale).toBe(expectedScale);
  });

  test("When a user clicks on the plus icon to zoom in on an axis, Then the specified scale should divide by 1.5", async () => {
    const wrapper = mount(StimulationStudioZoomControls, {
      localVue,
      store,
      propsData: {
        axis: "y-axis",
      },
    });
    const expectedScale = 80;
    expect(store.state.stimulation.yAxisScale).toBe(120);
    await wrapper.find(".span__axis-controls-zoom-in-button").trigger("click");
    expect(store.state.stimulation.yAxisScale).toBe(expectedScale);
  });
});
