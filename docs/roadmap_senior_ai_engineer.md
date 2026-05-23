# Roadmap สู่ Senior AI Engineer ระดับโลก

โดย Thanarat · 2026

นี่คือเส้นทางที่ผมแนะนำ จากประสบการณ์การทำโปรเจกต์นี้และจากที่เห็น
engineer ระดับโลกทำงานจริง. ไม่ใช่ทฤษฎีอย่างเดียว ทุกข้อมีของให้ทำตาม.

---

## ระดับ 0: คณิตศาสตร์พื้นฐานที่ขาดไม่ได้ (1-2 เดือน)

ไม่ต้องเป็นนักคณิตศาสตร์ แต่ถ้าไม่เข้าใจ 4 หัวข้อนี้ คุณจะแค่ "copy code"
ไม่มีวันได้เลื่อนเป็น Senior

1. **Linear Algebra** (matrix, vector, dot product, eigenvalue)
   - Course: MIT 18.06 Linear Algebra (Gilbert Strang) บน YouTube ฟรี
   - ทำเข้าใจ: ภาพ = matrix, neural network layer = matrix multiplication

2. **Calculus** (derivative, chain rule, partial derivative)
   - คือสมการที่อยู่เบื้องหลัง `loss.backward()`
   - Course: 3Blue1Brown "Essence of Calculus" YouTube ดูได้ภายใน 3 ชม.

3. **Probability + Statistics** (mean, variance, distribution, Bayes)
   - ใช้ทุกที่ใน ML
   - Book: "Think Stats" by Allen Downey (ฟรี online)

4. **Optimization** (gradient descent, convex vs non-convex)
   - หัวใจของการเทรนทุก neural network
   - Visualize: https://distill.pub/2017/momentum/

---

## ระดับ 1: Python + Deep Learning Fundamentals (2-3 เดือน)

### Python ระดับที่ต้องมี
- NumPy คล่อง: vectorize, broadcasting
- PyTorch (ไม่ใช่ TensorFlow แล้ว ส่วนใหญ่ของวงการตอนนี้ใช้ PyTorch)
- pandas, matplotlib เพื่อ EDA (exploratory data analysis)

### Deep Learning concepts ที่ต้องเข้าใจลึก
- [ ] Perceptron → Multi-layer perceptron (MLP)
- [ ] Activation functions (ReLU, Sigmoid, Tanh, GELU, Swish)
- [ ] Loss functions (Cross-entropy, MSE, CTC, Focal, Triplet)
- [ ] Optimizers (SGD, Adam, AdamW, Lion, Adafactor)
- [ ] Regularization (L1/L2, Dropout, BatchNorm, LayerNorm)
- [ ] Training loop จริงๆ ทำงานยังไง (อย่าง file training_explained.py)

### โปรเจกต์ทำตาม
1. **MNIST จากศูนย์ด้วย NumPy** (ไม่ใช้ framework)
   ห้าม PyTorch! เขียน forward + backward เอง
   ทำได้ = เข้าใจ deep learning จริง

2. **เทรน CNN จาก scratch บน CIFAR-10**
   ใช้ PyTorch แต่เขียน model เอง ไม่ใช้ pretrained

3. **โปรเจกต์ของเรา Deep ALPR**
   อ่าน [training_explained.py](training_explained.py) ทุกบรรทัด
   เปลี่ยน learning rate / batch size / model size ดูผล

### Course แนะนำ
- **fast.ai** course "Practical Deep Learning" ฟรี เป็น top tier
- **deeplearning.ai** Andrew Ng (เก่าหน่อยแต่พื้นฐานดี)
- **Karpathy YouTube** ดูทุก video ของ Andrej Karpathy โดยเฉพาะ
  "Let's build GPT" และ "micrograd"

---

## ระดับ 2: Computer Vision เฉพาะทาง (2-3 เดือน)

ที่โปรเจกต์ของเราใช้:

- [ ] **CNN architectures**: LeNet, AlexNet, VGG, ResNet, EfficientNet
- [ ] **Object Detection**: R-CNN family, YOLO family (v1-v11), SSD, DETR
- [ ] **Segmentation**: U-Net, Mask R-CNN, Segment Anything
- [ ] **OCR**: CRNN (ของเรา), Transformer OCR, TrOCR
- [ ] **Vision Transformers**: ViT, Swin, DINO

### โปรเจกต์
1. **Fine-tune YOLOv8/v11 บน custom dataset** ของตัวเอง
2. **อ่าน paper "CRNN: An End-to-End Trainable Neural Network..."** ของ Shi 2015
   แล้ว implement จาก scratch (เหมือนที่เราใช้ในโปรเจกต์นี้)
3. **Implement Vision Transformer (ViT) จาก scratch**
   ทำได้ = เข้าใจ Transformer architecture

---

## ระดับ 3: Modern AI (Transformers + LLM) (3-6 เดือน)

ปี 2026 ถ้าคุณไม่เข้าใจ Transformer = ไม่ใช่ Senior

- [ ] **Attention mechanism** (อ่าน paper "Attention Is All You Need")
- [ ] **Transformer architecture**: self-attention, multi-head, positional encoding
- [ ] **Tokenization**: BPE, SentencePiece, WordPiece
- [ ] **Pre-training vs Fine-tuning**: MLM, CLM, instruction tuning
- [ ] **LLM specifics**: RLHF, DPO, LoRA, QLoRA, RAG
- [ ] **Inference optimization**: quantization, distillation, flash-attention

### โปรเจกต์
1. **"Let's build GPT" ของ Karpathy** ทำจนเสร็จ
2. **Fine-tune Llama 3 ด้วย LoRA** บน custom dataset
3. **Build RAG system** กับ Thai documents

---

## ระดับ 4: Production / MLOps (ตลอดอาชีพ)

ที่แยก "Senior" จาก "นักวิจัย":

- [ ] **Data pipeline**: collection, annotation, versioning (DVC)
- [ ] **Experiment tracking**: Weights & Biases, MLflow
- [ ] **Model versioning + registry**
- [ ] **Deployment**: ONNX, TensorRT, serving (Triton, TorchServe)
- [ ] **Monitoring**: drift detection, performance tracking
- [ ] **Distributed training**: DDP, FSDP, DeepSpeed
- [ ] **Cost optimization**: spot instances, mixed precision (fp16/bf16)

### โปรเจกต์
1. **Deploy โปรเจกต์ Deep ALPR ของเราขึ้น production**
   - ใช้ Docker
   - vCPU instance + GPU spot instance
   - Add monitoring (Prometheus + Grafana)
   - Auto-retraining pipeline ทุก 3 เดือน

---

## ระดับ 5: Research Reading + Contribution

Senior ระดับโลกอ่าน paper สม่ำเสมอ.

- [ ] **อ่าน paper สัปดาห์ละ 2-3 ฉบับ**
  เริ่มจาก seminal: ResNet, Transformer, BERT, GPT-3, CLIP, Diffusion
- [ ] **ติดตาม conference**: NeurIPS, ICML, ICLR, CVPR, ACL
- [ ] **Subscribe**: arXiv-sanity, Papers With Code, Hugging Face daily papers
- [ ] **Open source contribution**: submit PR ไป Hugging Face Transformers,
      PyTorch, หรือ project ที่ใช้บ่อย
- [ ] **เขียน blog post / paper เอง**

---

## Tools และ Stack มาตรฐานปี 2026

| Category | Tool | ใช้เมื่อ |
|---|---|---|
| Framework | PyTorch | default |
| Training | Lightning, Accelerate | scale-up |
| Experiment | Weights & Biases | ทุก project |
| Vision | Ultralytics (YOLO), Timm | computer vision |
| NLP | Hugging Face Transformers | text/LLM |
| Vector DB | Qdrant, Weaviate | RAG |
| Deployment | ONNX Runtime, TensorRT | edge |
| Serving | Triton, vLLM, TGI | cloud |
| MLOps | MLflow, DVC | enterprise |

---

## Mindset ของ Senior AI Engineer ระดับโลก

1. **อ่าน code คนอื่นเยอะกว่าเขียนเอง**
   เปิด PyTorch source อ่านจริง อ่าน Hugging Face implementation

2. **Reproduce paper ก่อน improve**
   ถ้าทำ paper ที่อ่านมาให้ run ได้ผลเดิมไม่ได้ อย่ารีบไปต่อ

3. **วัดผลก่อนตัดสินใจ**
   "เพราะรู้สึกว่าดี" ≠ benchmark. ทำ A/B test เสมอ

4. **เข้าใจ data ก่อน model**
   ใช้เวลา 80% กับ data, 20% กับ model. Senior ที่แท้จริงทำแบบนี้

5. **เขียน documentation เหมือนเขียน code**
   ไม่มี doc = code ตายตอนคุณลาออก

6. **ไม่กลัวจะถูกพิสูจน์ว่าผิด**
   model ของคุณ accuracy 99.6%? เอามาเทสกับข้อมูลใหม่ที่ผมยังไม่ให้เห็น
   ถ้าตกลงต่ำ ยอมรับและไปแก้

7. **เข้าใจ business เหมือนกัน**
   "accuracy 95%" ดีหรือไม่ดี ขึ้นกับว่า cost ของผิดเป็นอะไร
   ผิดในการอ่านป้ายให้คนผ่านประตู vs ผิดในการวินิจฉัยมะเร็ง

---

## เกณฑ์ตอบโจทย์ "Senior AI Engineer ระดับโลก"

Junior:
- รู้จัก concept
- รัน code ที่คนอื่นเขียนได้

Mid:
- เขียน training pipeline เองได้
- debug ได้

Senior (Thailand):
- design architecture ใหม่ตามปัญหา
- optimize ทั้ง accuracy + cost
- mentor junior

Senior (World-class / ตำแหน่งที่ Google, OpenAI, Anthropic):
- ตีพิมพ์ paper top venue
- หรือ ship product ที่ใช้คนเป็นล้าน
- เข้าใจทั้ง systems (CUDA, distributed) และ research
- ภาษาอังกฤษระดับ communicate กับ research community ได้

---

## Action plan สำหรับ 12 เดือนข้างหน้า

- **เดือน 1-2**: ทำ math + Python ให้แน่น
- **เดือน 3-4**: ทำ MNIST จากศูนย์ + fast.ai course
- **เดือน 5-6**: ทำโปรเจกต์ CV จาก scratch 2-3 ตัว
- **เดือน 7-8**: deploy โปรเจกต์ Deep ALPR ขึ้น production จริง
- **เดือน 9-10**: เรียน Transformer + LLM
- **เดือน 11-12**: contribute open source + เขียน blog 5 ตัว

ปลายปีถ้าทำตาม คุณจะ apply ตำแหน่ง Senior AI Engineer ใน startup ระดับ
World-class ได้แล้ว.

---

## หนังสือที่ Senior ทุกคนอ่าน

1. **Deep Learning** by Goodfellow, Bengio, Courville (ฟรี online)
2. **The Hundred-Page Machine Learning Book** by Andriy Burkov
3. **Designing Machine Learning Systems** by Chip Huyen
4. **Hands-On Machine Learning** by Aurelien Geron (practical guide)
5. **Pattern Recognition and Machine Learning** by Bishop (classic)

ของไทย:
- ไม่มีเล่มไหนเทียบเล่มภาษาอังกฤษได้ ลงทุนเรียนภาษาอังกฤษ

---

โปรเจกต์ Deep ALPR ที่คุณทำอยู่ตอนนี้ คือ Mid → Senior level project แล้ว.
ถ้า deploy production จริง + train จาก real data + write technical blog
จะเป็นพอร์ตที่ Senior World-class ดูแล้วประทับใจ.

ผมเชื่อว่าคุณทำได้.
