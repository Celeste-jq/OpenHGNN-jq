from openhgnn.model.NSHE import NSHE
from openhgnn.utils.trainer import run, run_GTN, run_RSHN, run_RGCN
from openhgnn.utils.evaluater import evaluate
from openhgnn.utils.dgl_graph import load_HIN, load_KG
import torch as th

def OpenHGNN(config):
    # load the graph(HIN or KG)
    if config.model in ['GTN', 'NSHE']:
        g = load_HIN(config.dataset).to(config.device)
    elif config.model in ['RSHN', 'RGCN']:
        kg, category, num_classes = load_KG(config.dataset)
        config.category = category
        config.num_classes = num_classes
        kg = kg.to(config.device)

    # select the model
    if config.model == 'GTN':
        if config.sparse_flag == 'True':
            from openhgnn.model.GTN_sparse import GTN
            model = GTN(num_edge=5,
                        num_channels=config.num_channels,
                        w_in=g.ndata['h']['paper'].shape[1],
                        w_out=config.emd_size,
                        num_class=3,
                        num_layers=config.num_layers)
        else:
            from openhgnn.model.GTN import GTN
            model = GTN(num_edge=5,
                        num_channels=config.num_channels,
                        w_in=g.ndata['h']['paper'].shape[1],
                        w_out=config.emd_size,
                        num_class=3,
                        num_layers=config.num_layers,
                        norm=None)
        model.to(config.device)
        # train the model
        node_emb = run_GTN(model, g, config)  # 模型训练
    elif config.model == 'NSHE':
        model = NSHE(g=g, gnn_model="GCN", project_dim=config.dim_size['project'],
                 emd_dim=config.dim_size['emd'], context_dim=config.dim_size['context']).to(config.device)
        run(model, g, config)
    elif config.model == 'RSHN':
        from openhgnn.model.RSHN import RSHN
        from openhgnn.utils.dgl_graph import coarsened_line_graph
        cl = coarsened_line_graph(rw_len=config.rw_len, batch_size=config.batch_size, n_dataset=config.dataset, symmetric=True)
        cl_graph = cl.get_cl_graph(kg).to(config.device)
        cl_graph = cl.init_cl_graph(cl_graph)
        model = RSHN(in_feats1=kg.num_nodes(), in_feats2=cl_graph.num_nodes(), dim=config.dim, num_classes=config.num_classes, num_node_layer=config.num_node_layer,
                     num_edge_layer=config.num_edge_layer, dropout=config.dropout).to(config.device)
        run_RSHN(model, kg, cl_graph, config)
    elif config.model == 'RGCN':
        # create model
        from openhgnn.model.RGCN import EntityClassify
        model = EntityClassify(kg.number_of_nodes(),
                               config.n_hidden,
                               config.num_classes,
                               len(kg.canonical_etypes),
                               num_bases=config.n_bases,
                               num_hidden_layers=config.n_layers - 2,
                               dropout=config.dropout,
                               use_self_loop=config.use_self_loop,use_cuda=True).to(config.device)
        run_RGCN(model, kg, config)


    print("Train finished")
    # evaluate the performance
    # evaluate(config.seed, config.dataset, node_emb, g)
    return

