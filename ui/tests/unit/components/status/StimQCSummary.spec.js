import { mount } from "@vue/test-utils";
import StimQCSummary from "@/components/status/StimQCSummary.vue";
import { createLocalVue } from "@vue/test-utils";
const localVue = createLocalVue();
let NuxtStore;
let store;

describe("StimQCSummary.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });
  test("When that StimQCSummary is visible, Then it will display correct configuration check messages", async () => {
    const wrapper = mount(StimQCSummary, {
      localVue,
      store,
    });
    const targetHeaderText = wrapper.find(".span__stimqc-label");
    const targetMessageSpanP = wrapper.findAll("p");

    expect(targetHeaderText.text()).toStrictEqual("Configuration Check Summary!");
    expect(targetMessageSpanP.at(0).text()).toStrictEqual(
      "An open circuit was detected in the assigned wells shown below. This will prevent you from being able to start a stimulation."
    );
    expect(targetMessageSpanP.at(1).text()).toStrictEqual("Please unassign these wells before proceeding.");
  });
  test("Given that StimQCSummary is mounted, When the StimQCSummary is visible, Then click on 'Okay results in an event 'handle-confirmation' to be emitted", async () => {
    const wrapper = mount(StimQCSummary, {
      localVue,
      store,
    });
    const cancelYesBtn = wrapper.findAll(".span__button-label");
    await cancelYesBtn.at(0).trigger("click");
    const yesBtnEvents = wrapper.emitted("handle-confirmation");
    expect(yesBtnEvents[0]).toStrictEqual([0]);
  });
});
