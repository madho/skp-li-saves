(() => {
  const CARD_SELECTOR = '[data-chameleon-result-urn]';
  const BUTTON_TEXT = /show more results/i;
  const DOWNLOAD_NAME = 'linkedin_saved_posts.json';

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const mergeUrns = () => {
    window.__urns = window.__urns || new Set();
    document.querySelectorAll(CARD_SELECTOR).forEach((node) => {
      const urn = node.getAttribute('data-chameleon-result-urn');
      if (urn) window.__urns.add(urn);
    });
    return window.__urns.size;
  };

  const clickShowMore = () => {
    const buttons = [...document.querySelectorAll('button, a, span, div')].filter((node) =>
      BUTTON_TEXT.test((node.textContent || '').trim())
    );
    const button = buttons.find((node) => typeof node.click === 'function');
    if (button) {
      button.click();
      return true;
    }
    return false;
  };

  const downloadJson = () => {
    const rows = [...document.querySelectorAll(CARD_SELECTOR)].map((node) => ({
      urn: node.getAttribute('data-chameleon-result-urn') || '',
      text: node.innerText || '',
    }));
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' });
    const anchor = document.createElement('a');
    anchor.href = URL.createObjectURL(blob);
    anchor.download = DOWNLOAD_NAME;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
    return rows.length;
  };

  const run = async () => {
    window.__urns = new Set();
    let previousCount = 0;
    let stalledPasses = 0;

    while (stalledPasses < 4) {
      window.scrollTo(0, document.body.scrollHeight);
      window.dispatchEvent(new WheelEvent('wheel', { deltaY: 1200, bubbles: true, cancelable: true }));
      await sleep(1200);
      mergeUrns();

      const currentCount = window.__urns.size;
      const clicked = clickShowMore();
      if (clicked) {
        await sleep(1200);
        mergeUrns();
      }

      if (currentCount <= previousCount && !clicked) {
        stalledPasses += 1;
      } else {
        stalledPasses = 0;
      }
      previousCount = currentCount;

      console.log(`LinkedIn saved posts captured so far: ${currentCount}`);
    }

    const downloaded = downloadJson();
    console.log(`Downloaded ${downloaded} cards to ${DOWNLOAD_NAME}`);
    return downloaded;
  };

  window.__mergeLinkedInSavedPosts = mergeUrns;
  window.__downloadLinkedInSavedPosts = downloadJson;
  window.__runLinkedInSavedPostsCapture = run;

  console.log('Loaded LinkedIn saved-posts capture helper. Run __runLinkedInSavedPostsCapture() to scroll, merge, and download JSON.');
})();
