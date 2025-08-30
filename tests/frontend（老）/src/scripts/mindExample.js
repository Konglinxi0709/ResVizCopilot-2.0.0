const example = {
    nodeData: {
      id: "me-root",
      topic: "",
      style: {
        background: "transparent",
      },
      image: {
        // 添加图片到节点，添加图片时，必须填写宽高
        url: require("../assets/mind.png"),  // 图片链接
        width: 100,
        height: 100,
      },
      children: [
        {
          topic: "What is Mind Elixir",
          id: "bd4313fbac40284b",
          direction: 0,
          children: [
            {
              topic: "A mind map core",
              id: "beeb823afd6d2114",
              dangerouslySetInnerHTML: `<div class="el-input__wrapper" tabindex="-1"><!-- prefix slot --><!--v-if--><input class="el-input__inner" type="text" autocomplete="off" tabindex="0" placeholder="输入检索表达式" id="el-id-1147-3"><!-- suffix slot --><!--v-if--></div>`
            },
            {
              topic: "Free",
              id: "c1f068377de9f3a0"
            },
            {
              topic: "Open-Source",
              id: "c1f06d38a09f23ca"
            },
            {
              topic: "Use without JavaScript framework",
              id: "c1f06e4cbcf16463",
              children: []
            },
            {
              topic: "Use in your own project",
              id: "c1f1f11a7fbf7550",
              children: [
                {
                  topic: "import MindElixir from 'mind-elixir'",
                  id: "c1f1e245b0a89f9b",
                  tags: ["AI"]
                },
                {
                  topic: "new MindElixir({...}).init(data)",
                  id: "c1f1ebc7072c8928",
                  tags: ["AI"]
                }
              ]
            },
            {
              topic: "Easy to use",
              id: "c1f0723c07b408d7",
              children: [
                {
                  topic: "Use it like other mind map application",
                  id: "c1f09612fd89920d"
                }
              ]
            }
          ]
        },
      ],
      
    },
    direction: 1,
    theme: {
      name: "Latte",
      palette: ["#dd7878", "#ea76cb", "#8839ef", "#e64553", "#fe640b", "#df8e1d", "#40a02b", "#209fb5", "#1e66f5", "#7287fd"],
      cssVar: {
        "--main-color": "#444446",
        "--main-bgcolor": "#ffffff",
        "--color": "#777777",
        "--bgcolor": "#f6f6f6",
        "--panel-color": "#444446",
        "--panel-bgcolor": "#ffffff",
        "--panel-border-color": "#eaeaea"
      }
    }
  };

export default example