import os, sys, time
from PIL import Image, ImageDraw
SUF = (", single creature, full body, side three-quarter view, isolated on pure white background, "
       "no ground, no floor, no shadow, no base, no pedestal, no text")
STY = ["realistic wildlife illustration", "detailed naturalistic 3D render", "scientific anatomical illustration"]
A = {
 "wolf": ["a grey wolf standing on all four legs, lean deep chest, long legs, bushy tail hanging down, ears erect, long muzzle",
          "a gray timber wolf standing, four legs straight, narrow body, thick neck ruff, tail low, pointed ears"],
 "horse": ["a chestnut horse standing on four long slender legs, muscular neck arched, flowing mane and tail, hooves visible",
           "a bay thoroughbred horse standing square, long legs, deep chest, arched neck, dark mane and tail"],
 "elephant": ["an African elephant standing on four thick pillar legs, large fan ears, long trunk hanging to the ground, curved white tusks",
              "an adult African bush elephant standing, massive body, huge ears, long trunk, ivory tusks, thin tail"],
 "giraffe": ["a giraffe standing, extremely long neck as long as its legs, straight back sloping down from high shoulders to low hips, no hump, small head with two ossicones, long thin legs, patchy brown coat",
             "a reticulated giraffe standing tall, very long straight neck, back slopes in a straight line from tall withers to low rump, long slender legs, tiny ossicones on head"],
 "crocodile": ["a Nile crocodile lying flat on its belly, sprawling posture, short legs splayed out sideways, long low flat body, long heavy tail, long flat snout, horizontal body close to the ground",
               "a crocodile crawling low, belly almost touching the ground, four short legs bent out to the sides, long armored scaly body and tail stretched out horizontally, elongated jaws"],
 "eagle (perched)": ["a bald eagle perched upright, wings folded against body, white head, hooked yellow beak, talons gripping, tail feathers pointing down",
                     "a golden eagle sitting perched, folded wings, upright stance, sharp hooked beak, feathered legs, strong talons"],
 "shark": ["a great white shark swimming, torpedo-shaped body, tall triangular dorsal fin, pectoral fins, crescent tail fin, horizontal",
           "a great white shark, streamlined body, grey back white belly, dorsal fin, long pectoral fins, forked tail, side view"],
 "frog": ["a green tree frog sitting, folded hind legs, front legs upright, big round eyes, smooth skin",
          "a bullfrog crouching, long folded back legs, short front legs, wide mouth, bulging eyes"],
 "tortoise": ["a giant tortoise walking, high domed shell, thick elephant-like scaly legs, wrinkled neck extended, small head",
              "a Galapagos tortoise standing, large domed carapace, stout legs, head and neck out of shell"],
 "kangaroo": ["a red kangaroo standing upright on large hind legs, long thick tail touching ground behind as support, small forearms, long ears",
              "a kangaroo standing, powerful hind legs and long feet, thick tapered tail, short arms held in front, upright torso"],
}
def grid(d, n):
    ims = [Image.open(f"{d}/c{k}.png").resize((320,320)) for k in range(n)]
    cols = 6; rows = (n+cols-1)//cols
    g = Image.new("RGB", (320*cols, 340*rows), "white"); dr = ImageDraw.Draw(g)
    for k, im in enumerate(ims):
        x, y = (k%cols)*320, (k//cols)*340
        g.paste(im, (x, y+20)); dr.text((x+5, y+3), f"c{k}", fill="black")
    g.save(f"{d}/grid.png")
def prompts(name):
    p = A[name]; return [f"{p[k%2]}, {STY[k%3]}" + SUF for k in range(6)]
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "hy"
    names = sys.argv[2].split(",") if len(sys.argv) > 2 else list(A)
    if mode == "hy":
        from hy3dgen.text2image import HunyuanDiTPipeline
        t2i = HunyuanDiTPipeline("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled")
        for n in names:
            d = f"r7/{n.split(' ')[0]}"; os.makedirs(d, exist_ok=True)
            for k, p in enumerate(prompts(n)):
                t2i(p, seed=100+k).save(f"{d}/c{k}.png"); print(n, k, p, flush=True)
            grid(d, 6)
    else:  # flux for c6..c11
        import torch
        from diffusers import FluxPipeline
        pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16).to("cuda")
        for n in names:
            d = f"r7/{n}"; name = n
            for k, p in enumerate(prompts(name)):
                im = pipe(p, num_inference_steps=4, guidance_scale=0.0, height=1024, width=1024,
                          max_sequence_length=256, generator=torch.manual_seed(200+k)).images[0]
                im.save(f"{d}/c{6+k}.png"); print(n, 6+k, p, flush=True)
            grid(d, 12)
