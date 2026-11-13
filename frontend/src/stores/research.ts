import {createStore} from '../utils/store';import * as runs from '../api/runs';import * as proposals from '../api/proposals';import * as sensitivity from '../api/sensitivity';import type {Run,Proposal,Sensitivity} from '../types/domain';
export const researchStore=createStore<{runs:Run[];proposals:Proposal[];sensitivities:Sensitivity[];selected:number;selectedSensitivity:number}>({runs:[],proposals:[],sensitivities:[],selected:Number(localStorage.getItem('pairwise-run')||0),selectedSensitivity:0});
export async function loadRuns(){const items=await runs.list();let selected=researchStore.get().selected;if(!items.some(r=>r.id===selected))selected=items.find(r=>r.status==='completed')?.id||items[0]?.id||0;researchStore.set({runs:items,selected});}
export function selectRun(selected:number){localStorage.setItem('pairwise-run',String(selected));researchStore.set({selected,selectedSensitivity:0});}
export async function queue(data:unknown){const r=await runs.create(data);await loadRuns();selectRun(r.id);return r;}
export async function loadSensitivity(){const items=await sensitivity.list();const {selected,selectedSensitivity}=researchStore.get();const mine=items.filter(s=>s.run_id===selected);researchStore.set({sensitivities:items,selectedSensitivity:mine.some(s=>s.id===selectedSensitivity)?selectedSensitivity:mine[0]?.id||0});}
export function selectSensitivity(selectedSensitivity:number){researchStore.set({selectedSensitivity});}
export async function queueSensitivity(data:unknown){const s=await sensitivity.create(data);await loadSensitivity();selectSensitivity(s.id);return s;}
export async function loadProposals(){researchStore.set({proposals:await proposals.list()});}
export async function addProposal(data:unknown){const p=await proposals.create(data);await loadProposals();return p;}
export async function reviewProposal(id:number,status:string,note:string){await proposals.review(id,status,note);await loadProposals();}
