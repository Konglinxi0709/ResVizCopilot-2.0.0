const initialMindMapData = {
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
    children: []
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

export default initialMindMapData; 