/**
 * 依 VITE_DEMO_MODE 切換使用真後端 API 或本機 Demo/Fixture 模擬 API。
 * 其餘元件一律從這裡 import，不直接依賴 api.js 或 demoApi.js，
 * 之後要切換／移除 Demo 模式只需要改這一個檔案。
 */
import * as realApi from "./api";
import * as demoApi from "./demoApi";

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

const impl = DEMO_MODE ? demoApi : realApi;

export const createJob = impl.createJob;
export const getJob = impl.getJob;
export const trackUrl = impl.trackUrl;
export const thumbnailUrl = impl.thumbnailUrl;
