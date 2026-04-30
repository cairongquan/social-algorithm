<script setup lang="ts">
interface Props {
  text?: string
}

const props = withDefaults(defineProps<Props>(), {
  text: '暂无数据'
})
</script>

<template>
  <div class="empty-state" role="status" aria-live="polite">
    <div class="flower-wrap" aria-hidden="true">
      <div class="stem"></div>
      <div class="leaf leaf-left"></div>
      <div class="leaf leaf-right"></div>
      <div class="petal petal-1"></div>
      <div class="petal petal-2"></div>
      <div class="petal petal-3"></div>
      <div class="petal petal-4"></div>
      <div class="core"></div>
      <div class="ground"></div>
    </div>
    <p class="empty-text">{{ props.text }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  margin: 56px auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #000000;
}

.flower-wrap {
  position: relative;
  width: 150px;
  height: 170px;
}

.stem {
  position: absolute;
  left: 76px;
  top: 62px;
  width: 2px;
  height: 72px;
  background: #000000;
  transform: rotate(12deg);
  transform-origin: top center;
}

.leaf {
  position: absolute;
  width: 28px;
  height: 10px;
  border: 1px solid #000000;
  border-radius: 0;
  background: #ffffff;
}

.leaf-left {
  left: 48px;
  top: 96px;
  transform: rotate(-24deg);
}

.leaf-right {
  left: 78px;
  top: 108px;
  transform: rotate(32deg);
}

.petal {
  position: absolute;
  width: 26px;
  height: 14px;
  border: 1px solid #000000;
  background: #ffffff;
  transform-origin: 2px 7px;
}

.petal-1 {
  left: 64px;
  top: 44px;
  transform: rotate(38deg);
}

.petal-2 {
  left: 78px;
  top: 36px;
  transform: rotate(78deg);
}

.petal-3 {
  left: 90px;
  top: 48px;
  transform: rotate(118deg);
}

.petal-4 {
  left: 84px;
  top: 62px;
  transform: rotate(152deg);
}

.core {
  position: absolute;
  left: 77px;
  top: 54px;
  width: 8px;
  height: 8px;
  border: 1px solid #000000;
  background: #000000;
}

.ground {
  position: absolute;
  left: 30px;
  top: 136px;
  width: 92px;
  height: 1px;
  background: #000000;
}

.empty-text {
  margin-top: 10px;
  font-size: 16px;
  letter-spacing: 0.08em;
}
</style>
