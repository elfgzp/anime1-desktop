import { test, expect } from "../fixtures";
import type { Page } from "@playwright/test";

test.describe("真实 m3u8 视频播放", () => {
  test("应该能够搜索超时空并播放 m3u8 视频", async ({ window }) => {
    test.setTimeout(120000);

    await window.waitForSelector('input[placeholder="搜索番剧..."]', {
      timeout: 10000,
    });
    const searchInput = window.locator('input[placeholder="搜索番剧..."]');
    await searchInput.fill("超时空");
    await searchInput.press("Enter");

    await window.waitForSelector(".anime-card", { timeout: 15000 });

    const animeCardCount = await window.locator(".anime-card").count();
    console.log(`Found ${animeCardCount} anime cards`);
    expect(animeCardCount).toBeGreaterThan(0);

    await window.locator(".anime-card").first().click();

    await window.waitForSelector(".episode-card", { timeout: 15000 });

    const episodeCardCount = await window.locator(".episode-card").count();
    console.log(`Found ${episodeCardCount} episode cards`);
    expect(episodeCardCount).toBeGreaterThan(0);

    await window.locator(".episode-card").first().click();

    await window.waitForSelector("video", { timeout: 15000 });

    const videoSrc = await window.locator("video").getAttribute("src");
    console.log("Video src:", videoSrc);

    expect(videoSrc).toBeTruthy();
  });
});
