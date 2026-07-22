import * as THREE from 'three';

export interface DiceLightingRig {
  key: THREE.DirectionalLight;
  fill: THREE.DirectionalLight;
  rim: THREE.DirectionalLight;
  hemi: THREE.HemisphereLight;
  bounce: THREE.PointLight;
}

export const createDiceLighting = (scene: THREE.Scene): DiceLightingRig => {
  const hemi = new THREE.HemisphereLight(0xb8d3ff, 0x2a1d12, 0.48);

  const key = new THREE.DirectionalLight(0xfff5df, 1.8);
  key.position.set(4.4, 6.8, 7.6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 24;
  key.shadow.camera.left = -7;
  key.shadow.camera.right = 7;
  key.shadow.camera.top = 7;
  key.shadow.camera.bottom = -7;
  key.shadow.bias = -0.00022;
  key.shadow.normalBias = 0.02;

  const fill = new THREE.DirectionalLight(0x9dc7ff, 0.65);
  fill.position.set(-5.5, 3.8, 4.2);

  const rim = new THREE.DirectionalLight(0xf7edd8, 0.78);
  rim.position.set(1.2, 3.6, -6.2);

  const bounce = new THREE.PointLight(0xe6b987, 0.22, 18);
  bounce.position.set(0, -1.7, 0.4);

  scene.add(hemi, key, fill, rim, bounce);

  return { key, fill, rim, hemi, bounce };
};
