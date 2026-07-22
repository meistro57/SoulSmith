import * as THREE from 'three';
import { mergeVertices, toCreasedNormals } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

export interface GeometryPrepConfig {
  targetRadius: number;
  creaseAngleDeg: number;
}

const EPSILON = 1e-6;

const hasValidNormals = (geometry: THREE.BufferGeometry): boolean => {
  const normals = geometry.attributes.normal;
  if (!normals) {
    return false;
  }

  const array = normals.array;
  for (let index = 0; index < array.length; index += 3) {
    const x = array[index] as number;
    const y = array[index + 1] as number;
    const z = array[index + 2] as number;
    const lengthSquared = x * x + y * y + z * z;

    if (!Number.isFinite(lengthSquared) || lengthSquared < EPSILON) {
      return false;
    }
  }

  return true;
};

export const prepareDiceGeometry = (
  sourceGeometry: THREE.BufferGeometry,
  config: GeometryPrepConfig
): THREE.BufferGeometry => {
  const centeredGeometry = sourceGeometry.clone();
  centeredGeometry.computeBoundingBox();
  centeredGeometry.center();

  const mergedGeometry = mergeVertices(centeredGeometry, 1e-5);
  mergedGeometry.computeBoundingBox();
  mergedGeometry.computeBoundingSphere();

  const boundingSphereRadius = mergedGeometry.boundingSphere?.radius ?? 1;
  const scale = config.targetRadius / Math.max(boundingSphereRadius, EPSILON);
  mergedGeometry.scale(scale, scale, scale);

  mergedGeometry.computeBoundingBox();
  mergedGeometry.computeBoundingSphere();

  const creaseAngleRadians = THREE.MathUtils.degToRad(config.creaseAngleDeg);
  const withCreases = toCreasedNormals(mergedGeometry, creaseAngleRadians);

  if (!hasValidNormals(withCreases)) {
    withCreases.computeVertexNormals();
  }

  return withCreases;
};
