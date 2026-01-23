<template>
  <div class="div__schedule-mode-modal-container">
    <div class="div__schedule-mode-title">Nautilai Sync Mode</div>
    <div class="div__schedule-mode-subtitle">
      This mode allows you to synchronize your stimulation with Nautilai's recordings
    </div>
    <div class="div__schedule-mode-header">How to use:</div>
    <div class="div__schedule-mode-step">
      1. Ensure the "Stimulate until Complete" option is selected for all assigned protocols.
    </div>
    <div class="div__schedule-mode-step">
      2. Select the "Nautilai Sync" option in the Stingray controller.
    </div>
    <div class="div__schedule-mode-step">
      3. Select "Wait for trigger" in the Advanced Settings of the Nautilai controller.
    </div>
    <div class="div__schedule-mode-step">
      4. Click "Start Recording" in the Nautilai controller. Perform this step first!
    </div>
    <div class="div__schedule-mode-step">
      5. Click "Start Stimulation" in the Stingray controller. Perform this step second!
    </div>
    <div class="div__schedule-mode-step">
      6. The system will automatically cycle through all segments, ensuring stimulation and recording start
      together at each sextant.
    </div>
    <div class="div__schedule-mode-header">How it works:</div>
    <img
      :src="require(`@/assets/img/StimScheduleModeDiagram-NautilaiSync.png`)"
      class="img__schedule-mode-diagram"
    />
    <div class="div__schedule-mode-close-btn" @click="$bvModal.hide('sync-mode-help')">Close</div>
  </div>
</template>
<script>
export default {
  name: "StimScheduleNautilaiSyncModeHelp",
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
}

.div__schedule-mode-header {
  padding-left: 130px;
  font-size: 27px;
  padding-bottom: 5px;
  padding-top: 5px;
}

.div__schedule-mode-step {
  padding-left: 136px;
  font-size: 18px;
  line-height: 19px;
}

.img__schedule-mode-diagram {
  position: absolute;
  top: 330px;
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
