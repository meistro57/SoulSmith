import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

export interface DiceEnvironmentState {
  texture: THREE.Texture;
  dispose: () => void;
}

export const createDiceEnvironment = (renderer: THREE.WebGLRenderer): DiceEnvironmentState => {
  const pmremGenerator = new THREE.PMREMGenerator(renderer);
  pmremGenerator.compileEquirectangularShader();

  const roomEnvironment = new RoomEnvironment();
  const environmentRenderTarget = pmremGenerator.fromScene(roomEnvironment, 0.04);
  roomEnvironment.dispose();

  return {
    texture: environmentRenderTarget.texture,
    dispose: () => {
      environmentRenderTarget.dispose();
      pmremGenerator.dispose();
    }
  };
};
