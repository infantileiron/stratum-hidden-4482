import {request} from './client';import type {Dataset,Observation} from '../types/entities';export const list=()=>request<Dataset[]>('/datasets');export const create=(data:unknown)=>request<Dataset>('/datasets','POST',data);
export type DatasetDetail=Dataset&{rows:Observation[]};
export const detail=(id:string)=>request<DatasetDetail>('/datasets/'+id);
