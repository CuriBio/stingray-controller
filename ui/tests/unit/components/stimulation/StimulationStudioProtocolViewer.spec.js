import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioProtocolViewer from "@/components/stimulation/StimulationStudioProtocolViewer.vue";
import StimulationStudioWaveform from "@/components/stimulation/StimulationStudioWaveform.vue";
import Vuex from "vuex";
import { convertXYArraysToD3Array } from "@/js-utils/WaveformDataFormatter.js";
import { TEST_PROTOCOL_ORDER_2 } from "@/tests/sample-stim-protocols/stim-protocols";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("StimulationStudioProtocolViewer.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });
  afterEach(() => jest.clearAllMocks());

  test("When user wants to zoom in on an axis in the Protocol Viewer, Then the scale will be divided by 1.5", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    const expectedScale = 80;
    await wrapper.find(".span__axis-controls-zoom-in-button").trigger("click");
    expect(wrapper.vm.yAxisScale).toBe(expectedScale);
    // should be unchanged
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);
  });

  test("When user wants to zoom out on an axis in the Protocol Viewer, Then the scale will be divided by 1.5", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    const expectedScale = 180;
    await store.commit("stimulation/setZoomOut", "y-axis");
    expect(wrapper.vm.yAxisScale).toBe(expectedScale);

    // should be unchanged
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);
  });

  test("When user wants to zoom out on the x-axis in the Protocol Viewer, Then the scale will change depending on the existing plot width", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);

    await wrapper.findAll(".span__axis-controls-zoom-out-button").at(1).trigger("click");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(150);

    await wrapper.setData({ dynamicPlotWidth: 1800 });

    await wrapper.findAll(".span__axis-controls-zoom-in-button").at(1).trigger("click");

    expect(wrapper.vm.dynamicPlotWidth).toBe(1800);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);
  });

  test("When user wants to zoom in on the x-axis in the Protocol Viewer, Then the scale will change depending on the existing plot width", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    const zoomInButton = wrapper.findAll(".span__axis-controls-zoom-in-button").at(1);

    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(100);

    await zoomInButton.trigger("click");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(66.66666666666667);

    await wrapper.setData({ xAxisSampleLength: 200 });

    await zoomInButton.trigger("click");
    expect(wrapper.vm.dynamicPlotWidth).toBe(1200);
    expect(wrapper.vm.xAxisSampleLength).toBe(200 / 1.5);
  });

  test("When a user deletes the protocol, Then all datapoints should be deleted", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    await store.commit("stimulation/setAxisValues", { xValues: [0, 0, 200], yValues: [0, 300, 300] });
    await store.commit("stimulation/resetState");
    expect(wrapper.vm.datapoints).toStrictEqual([]);
  });

  test("When a user adds to the protocol, Then corresponding repeat colors should be reassignment upon mutation", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_2);
    expect(wrapper.vm.repeatColors).toBe(store.state.stimulation.repeatColors);
  });

  test("When a user adds a delay repeat to the end of the protocol, Then it will mutation to state and will automatically update in the waveform graph", async () => {
    const wrapper = mount(StimulationStudioProtocolViewer, {
      store,
      localVue,
    });

    const testValue = 5;

    await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_2);
    await store.dispatch("stimulation/handleNewRestDuration", testValue);

    expect(wrapper.vm.delayBlocks).toBe(store.state.stimulation.delayBlocks);
    expect(wrapper.vm.delayBlocks).toStrictEqual([[1300240, 1300245]]);
  });
  describe("StimulationStudioWaveform.vue", () => {
    test("When a user the protocol, Then all datapoints should be deleted", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      const renderSpy = jest.spyOn(wrapper.vm, "renderPlot");
      wrapper.vm.$options.watch.dataPoints.call(wrapper.vm, [
        [1, 2],
        [2, 3],
      ]);
      wrapper.vm.$options.watch.xAxisSampleLength.call(wrapper.vm, 1000);
      wrapper.vm.$options.watch.yMin.call(wrapper.vm, 0);
      wrapper.vm.$options.watch.yMax.call(wrapper.vm, 100);

      expect(renderSpy).toHaveBeenCalledTimes(4);
    });

    test("When a user zooms in or zooms out of the x axis in waveform graph, Then the new graph width will be reflected and the number of the ticks of the axis will change accordingly", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      expect(wrapper.vm.frequencyOfXTicks).toBe(10);
      expect(wrapper.vm.div__waveformGraph_dynamicStyle).toStrictEqual({ width: "1280px" });

      await wrapper.setProps({ plotAreaPixelWidth: 1800 });

      expect(wrapper.vm.frequencyOfXTicks).toBe(15);
      expect(wrapper.vm.div__waveformGraph_dynamicStyle).toStrictEqual({ width: "1880px" });
    });

    test("When a user hovers over a waveoform tile, Then the corresponding section of the graph will be filled with light opacity", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_2);
      const { xAxisValues, yAxisValues } = store.state.stimulation;
      const dPoints = await convertXYArraysToD3Array(xAxisValues, yAxisValues);
      await wrapper.setProps({ dataPoints: dPoints });

      await store.dispatch("stimulation/onPulseMouseenter", { idx: 1 });

      const highlightLineNode = wrapper.find("#highlightLineNode");
      const highlightLinePath = highlightLineNode.findAll("path");

      expect(highlightLinePath).toHaveLength(1);
      expect(highlightLinePath.at(0).attributes().opacity).toBe(".25");
      expect(highlightLinePath.at(0).attributes().fill).toBe("#ffff2");
    });

    test("When a user leaves hover over a waveoform tile, Then the corresponding section of the graph will no longer be filled", async () => {
      const wrapper = mount(StimulationStudioWaveform, {
        store,
        localVue,
      });

      await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_2);
      const { xAxisValues, yAxisValues } = store.state.stimulation;
      const dPoints = await convertXYArraysToD3Array(xAxisValues, yAxisValues);
      await wrapper.setProps({ dataPoints: dPoints });

      await store.commit("stimulation/onPulseMouseleave");

      const highlightLineNode = wrapper.find("#highlightLineNode");
      const highlightLinePath = highlightLineNode.findAll("path");

      expect(highlightLinePath).toHaveLength(0);
    });
  });
});
