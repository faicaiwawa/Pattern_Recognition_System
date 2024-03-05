from lib.test.evaluation.environment import EnvSettings

def local_env_settings():
    settings = EnvSettings()

    # Set your local paths here.

    settings.davis_dir = ''
    settings.got10k_path = ''
    settings.got_packed_results_path = ''
    settings.got_reports_path = ''
    settings.lasot_path = ''
    settings.network_path = 'E:\\PromptVT\\lib\\test/networks/'    # Where tracking networks are stored.
    settings.nfs_path = ''
    settings.otb_path = 'E:\\FLSTT\\OTB100\\'
    settings.result_plot_path = 'E:\\PromptVT\lib\test/result_plots/'
    settings.results_path = 'E:\\PromptVT\\lib\\test/tracking_results/'    # Where to store tracking results
    settings.segmentation_path = 'E:\\PromptVT\\lib\\test/segmentation_results/'
    settings.tn_packed_results_path = ''
    settings.tpl_path = ''
    settings.trackingnet_path = ''
    settings.uav_path = ''
    settings.vot_path = '/home/qiuyang/datasets/VOT2020'
    settings.youtubevos_dir = ''
    settings.prj_dir = 'E:\\PromptVT'
    settings.save_dir = 'E:\\PromptVT'

    return settings

