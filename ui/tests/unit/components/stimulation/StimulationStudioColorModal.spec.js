import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioColorModal from "@/components/stimulation/StimulationStudioColorModal.vue";
import Vuex from "vuex";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

const nonGreenRanges = [...Array(71).keys(), ...[...Array(360).keys()].splice(170)];
const colorsToDisplay = nonGreenRanges
  .filter((hue) => hue % 23 === 0)
  .map((hue) => `hsla(${hue}, 100%, 50%, 1)`);

describe("StimulationStudioColorModal.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  test("When mounting StimulationStudioColorModal from the component file, Then there will be 12 color blocks to choose from", async () => {
    const wrapper = mount(StimulationStudioColorModal, {
      store,
      localVue,
      propsData: {
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });

    const colorBlocks = wrapper.findAll(".individualColorBlock");
    expect(colorBlocks).toHaveLength(12);
  });

  test("When a user selects 'Cancel', Then changePulseColor will be emitted with the original color", async () => {
    const wrapper = mount(StimulationStudioColorModal, {
      store,
      localVue,
      propsData: {
        currentColor: "hsla(100, 100%, 50%, 1)",
      },
    });

    const cancelButton = wrapper.findAll(".span__button-label").at(0);
    await cancelButton.trigger("click");

    const emitedtEvents = wrapper.emitted("changePulseColor");
    expect(emitedtEvents).toHaveLength(1);
    expect(emitedtEvents[0]).toStrictEqual(["hsla(100, 100%, 50%, 1)"]);
  });

  test.each(colorsToDisplay)(
    "When a user selects %s from the 12 colors, Then the new color will be emitted to parent component",
    async (color) => {
      const wrapper = mount(StimulationStudioColorModal, {
        store,
        localVue,
        propsData: {
          currentColor: "hsla(100, 100%, 50%, 1)",
        },
      });

      const colorIdx = colorsToDisplay.indexOf(color);
      const colorBlocks = wrapper.findAll(".individualColorBlock");

      await colorBlocks.at(colorIdx).trigger("click");
      const emitedtEvents = wrapper.emitted("changePulseColor");
      expect(emitedtEvents[0]).toStrictEqual([colorsToDisplay[colorIdx]]);
    }
  );
});
