import {request,post} from './client';import type {Sensitivity} from '../types/domain';
export const list=()=>request<Sensitivity[]>('/sensitivity'+'');
export const create=(data:unknown)=>post<Sensitivity>('/sensitivity',data);
export const detail=(id:number)=>request<Sensitivity>('/sensitivity/'+id);
