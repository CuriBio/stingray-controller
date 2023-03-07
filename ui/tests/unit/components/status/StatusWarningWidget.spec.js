import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/status/StatusWarningWidget.vue";
import { StatusWarningWidget as DistComponentToTest } from "@/dist/mantarray.common";

import { createLocalVue } from "@vue/test-utils";
let wrapper = null;
const localVue = createLocalVue();

describe("StatusWarningWidget.vue", () => {
  afterEach(() => wrapper.destroy());
  test("When mounting StatusWarningWidget from the build dist file, Then it loads successfully and the `Warning!` defined title text is rendered", () => {
    wrapper = mount(DistComponentToTest, {
      localVue,
    });
    const targetSpan = wrapper.find(".span__status-warning-label");
    expect(targetSpan.text()).toStrictEqual("Warning!");
  });
  test("Given that StatusWarningWidget is active, When the lifecyle hook mounted is created, Then it will display a confirmation message that operations are still in progress", async () => {
    wrapper = mount(ComponentToTest, {
      localVue,
    });
    const background = wrapper.find(".div__status-warning-background");
    const targetMessageSpan = wrapper.find(".span__status-warning-message");
    const targetMessageSpanP = targetMessageSpan.findAll("p");
    expect(targetMessageSpanP.at(0).text()).toStrictEqual("Operations are still in progress.");
    expect(targetMessageSpanP.at(1).text()).toStrictEqual("Are you sure you want to exit?");
    expect(background.attributes().style).toBe("height: 161px;");
  });
  test("Given that StatusWarningWidget is mounted, When the StatusWarningWidget is visible, Then click on 'Yes' or 'Cancel' results in an event 'handleWarningClosure' to be emitted", async () => {
    wrapper = mount(ComponentToTest, {
      localVue,
    });

    const cancelYesBtn = wrapper.findAll(".span__button-label");
    await cancelYesBtn.at(1).trigger("click");
    const yesBtnEvents = wrapper.emitted("handleConfirmation");
    expect(yesBtnEvents[0]).toStrictEqual([1]);

    await cancelYesBtn.at(0).trigger("click");
    expect(yesBtnEvents[1]).toStrictEqual([0]);
  });
});
