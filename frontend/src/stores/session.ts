import type {User} from '../types/entities';
export function savedUser():User|null {try{return JSON.parse(sessionStorage.getItem('stratum-user')||'null')}catch{return null}}
export function saveSession(token:string,user:User){sessionStorage.setItem('stratum-token',token);sessionStorage.setItem('stratum-user',JSON.stringify(user))}
export function clearSession(){sessionStorage.removeItem('stratum-token');sessionStorage.removeItem('stratum-user')}
