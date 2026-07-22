import * as THREE from 'three';

export interface ParticlePool {
  points: THREE.Points;
  spawnBurst: (origin: THREE.Vector3, color: string, count?: number) => void;
  update: (deltaSeconds: number) => void;
  dispose: () => void;
}

const MAX_PARTICLES = 140;

export const createParticlePool = (): ParticlePool => {
  const positions = new Float32Array(MAX_PARTICLES * 3);
  const colors = new Float32Array(MAX_PARTICLES * 3);
  const sizes = new Float32Array(MAX_PARTICLES);
  const lifetimes = new Float32Array(MAX_PARTICLES);
  const velocities = new Float32Array(MAX_PARTICLES * 3);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

  const material = new THREE.PointsMaterial({
    size: 0.045,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });

  const points = new THREE.Points(geometry, material);
  points.frustumCulled = false;

  const activateParticle = (index: number, origin: THREE.Vector3, tint: THREE.Color): void => {
    const i3 = index * 3;
    positions[i3] = origin.x;
    positions[i3 + 1] = origin.y;
    positions[i3 + 2] = origin.z;

    colors[i3] = tint.r;
    colors[i3 + 1] = tint.g;
    colors[i3 + 2] = tint.b;

    const theta = Math.random() * Math.PI * 2;
    velocities[i3] = Math.cos(theta) * (0.05 + Math.random() * 0.12);
    velocities[i3 + 1] = 0.08 + Math.random() * 0.16;
    velocities[i3 + 2] = Math.sin(theta) * (0.05 + Math.random() * 0.12);

    sizes[index] = 0.03 + Math.random() * 0.04;
    lifetimes[index] = 0.55 + Math.random() * 0.9;
  };

  const spawnBurst = (origin: THREE.Vector3, color: string, count = 12): void => {
    const tint = new THREE.Color(color);
    let spawned = 0;

    for (let index = 0; index < MAX_PARTICLES && spawned < count; index += 1) {
      if (lifetimes[index] <= 0) {
        activateParticle(index, origin, tint);
        spawned += 1;
      }
    }

    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;
  };

  const update = (deltaSeconds: number): void => {
    for (let index = 0; index < MAX_PARTICLES; index += 1) {
      if (lifetimes[index] <= 0) {
        continue;
      }

      lifetimes[index] = Math.max(0, lifetimes[index] - deltaSeconds);
      const i3 = index * 3;
      velocities[i3 + 1] -= 0.28 * deltaSeconds;
      positions[i3] += velocities[i3] * deltaSeconds;
      positions[i3 + 1] += velocities[i3 + 1] * deltaSeconds;
      positions[i3 + 2] += velocities[i3 + 2] * deltaSeconds;

      if (lifetimes[index] === 0) {
        sizes[index] = 0;
      }
    }

    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.size.needsUpdate = true;
  };

  const dispose = (): void => {
    geometry.dispose();
    material.dispose();
  };

  return { points, spawnBurst, update, dispose };
};
