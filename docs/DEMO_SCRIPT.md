# SnapShelf: 2-Minute Demo Script

## Before you go on stage

- [ ] `run.bat` is running and the badge shows **Live**
- [ ] One real product photo is ready on the desktop (a mug, shoe or bottle on a messy table works best)
- [ ] You have already processed that photo once, so Cloudinary has cached the AI results
- [ ] A backup screen recording of a full run is saved, in case the Wi-Fi fails
- [ ] Browser zoom is at 110 to 125% so the audience can read it
- [ ] The GitHub repo is open in a second tab

## Script

**0:00 to 0:20, the problem**
> "Small sellers lose hours on every product. They have to edit the photo, resize it for each platform, and write a title, description and tags. SnapShelf does all of that from one phone photo."

**0:20 to 1:10, live demo**
1. Drag the photo in. Leave the background on "AI suggestion". Click **Generate**.
2. While it loads: *"Gemma 4 is reading the photo while Cloudinary uploads it, both in parallel."*
3. Show the **listing card**: *"Gemma 4 wrote the title, the description, the features, the tags and the alt text, and it also picked this background colour."*
4. Drag the **before and after** slider.
5. Scroll through the **five images**: *"Cloudinary removed the background with AI, then made a white marketplace version, social sizes and a banner using generative fill."*

**1:10 to 1:40, how it works**
> "Each image is just a Cloudinary transformation URL: background removal, pad, generative fill, then f_auto and q_auto. So this photo is now [X]% smaller to deliver."

Point at the **Bandwidth saved** stat.

**1:40 to 2:00, open source**
> "It's MIT-licensed on GitHub and runs on Gemma 4, an open-weight model. We also packaged it as an Agent Skill, so any AI agent can list products with it."

Run `python skills/snapshelf/scripts/snapshelf.py photo.jpg` in a terminal if you have time.

## Likely judge questions

| Question | Answer |
|---|---|
| Why Gemma 4? | It's open-weight and multimodal, fast enough for an interactive tool, and it understands the product directly from the image. |
| What if Gemma returns bad JSON? | The output is validated and normalised (title length, tag count, colour format). If it fails completely, images are still produced and a warning is shown. |
| How do you handle slow AI transformations? | The browser retries while Cloudinary returns 423 during generation, and repeated requests are served from the CDN cache. |
| How are keys kept safe? | They live only in `.env`, which is git-ignored. Error messages are redacted, and a test scans the repo for leaked keys. |
| What's next? | Bulk upload, Shopify and WooCommerce export, and running Gemma locally for fully offline use. |
