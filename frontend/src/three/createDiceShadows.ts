import * as THREE from 'three';

export interface DiceShadowSetup {
  tablePlane: THREE.Mesh;
  contactPlane: THREE.Mesh;
}

export const createDiceShadows = (scene: THREE.Scene): DiceShadowSetup => {
  const tableMaterial = new THREE.MeshStandardMaterial({
    color: '#171924',
    roughness: 0.9,
    metalness: 0.05
  });

  const tablePlane = new THREE.Mesh(new THREE.PlaneGeometry(24, 10), tableMaterial);
  tablePlane.rotation.x = -Math.PI / 2;
  tablePlane.position.y = -0.5;
  tablePlane.receiveShadow = true;
  scene.add(tablePlane);

  const contactMaterial = new THREE.ShadowMaterial({
    opacity: 0.22
  });
  const contactPlane = new THREE.Mesh(new THREE.PlaneGeometry(24, 10), contactMaterial);
  contactPlane.rotation.x = -Math.PI / 2;
  contactPlane.position.y = -0.49;
  contactPlane.receiveShadow = true;
  scene.add(contactPlane);

  return { tablePlane, contactPlane };
};
