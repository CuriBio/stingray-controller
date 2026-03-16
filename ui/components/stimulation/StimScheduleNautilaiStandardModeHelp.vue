<template>
  <div class="div__schedule-mode-modal-container">
    <div class="div__schedule-mode-title">Standard Mode</div>
    <div class="div__schedule-mode-subtitle">
      This mode allows you to stimulate your entire plate all at once. If connected to a Nautilai, the
      stimulation will begin independently, ignoring any Nautilai recording and scheduling settings.
    </div>
    <div class="div__schedule-mode-header">How to use:</div>
    <div class="div__schedule-mode-step">
      1. Define the protocols however you please - they will be executed exactly as you define them.
    </div>
    <div class="div__schedule-mode-step">
      2. Select the "Standard" option as the Stimulation Mode in the Stingray 96 Controller.
    </div>
    <div class="div__schedule-mode-step">
      3. If you are planning to take a recording on Nautilai, ensure you select "Wait for Trigger" in the
      Advanced Settings<br />of the Nautilai Controller. You may click "Start Acquisition" before or after
      step 4.
    </div>
    <div class="div__schedule-mode-step">4. Click "Start Stimulation" in the Stingray 96 controller.</div>
    <div class="div__schedule-mode-step">
      5. Feel free to stop the stimulation at will - it will not affect Nautilai's recording.
    </div>
    <div class="div__schedule-mode-header">How it works:</div>
    <img
      :src="require(`@/assets/img/StimScheduleModeDiagram-Standard.png`)"
      class="img__schedule-mode-diagram"
    />
    <div class="div__schedule-mode-close-btn" @click="$bvModal.hide('std-mode-help')">Close</div>
  </div>
</template>
<script>
export default {
  name: "StimScheduleNautilaiStandardModeHelp",
};
</script>
<style scoped>
.div__schedule-mode-modal-container {
  position: absolute;
  width: 1300px;
  height: 800px;
  left: -522px;
  background-color: black;
  border: 1px solid #ddd;
  color: #fff;
}

.div__schedule-mode-title {
  padding-top: 18px;
  padding-bottom: 3px;
  text-align: center;
  font-size: 35px;
}

.div__schedule-mode-subtitle {
  text-align: center;
  font-size: 26px;
  line-height: 27px;
  padding: 5px 70px;
}

.div__schedule-mode-header {
  padding-left: 130px;
  font-size: 27px;
  padding-bottom: 5px;
  padding-top: 5px;
}

.div__schedule-mode-step {
  padding-left: 136px;
  padding-right: 60px;
  font-size: 18px;
  line-height: 19px;
}

.img__schedule-mode-diagram {
  position: absolute;
  top: 350px;
  left: 175px;
  width: 950px;
}

.div__schedule-mode-close-btn {
  position: absolute;
  display: flex;
  top: 733px;
  left: 530px;
  width: 240px;
  height: 50px;
  color: black;
  background-color: #b7b7b7;
  justify-content: center;
  align-items: center;
}

.div__schedule-mode-close-btn:hover {
  background: #b7b7b7c9;
  cursor: pointer;
}
</style>
